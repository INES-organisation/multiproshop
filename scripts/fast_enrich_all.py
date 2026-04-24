"""
Script d'enrichissement RAPIDE de tous les produits CJ
Optimisations:
- listV2 en batch (100 produits/appel) pour stock + prix
- ThreadPoolExecutor pour paralléliser les appels détails/variantes
- Skip intelligent des produits déjà enrichis récemment
- Sauvegarde par batch (pas commit à chaque produit)

Usage:
  python scripts/fast_enrich_all.py              # Enrichir tout
  python scripts/fast_enrich_all.py --force       # Forcer même si déjà enrichi
  python scripts/fast_enrich_all.py --stock-only   # Seulement les stocks (très rapide)
  python scripts/fast_enrich_all.py --workers 5    # 5 threads parallèles
"""
import sys
import os
import argparse
import json
import time
import logging
from pathlib import Path
# ThreadPoolExecutor retiré: séquentiel pour respecter rate limit CJ
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app
from extensions import db
from models.product import Product
from models.product_variant import ProductVariant
from services.api_providers.cj_dropshipping_optimized import CJDropshippingApiOptimized
from services.cj_sync_service import CjSyncService
from services.cj_variant_sync_service import CjVariantSyncService
from config import Config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

stats = {
    'stock_updated': 0,
    'details_updated': 0,
    'variants_synced': 0,
    'ratings_updated': 0,
    'skipped': 0,
    'errors': 0,
    'api_calls': 0,
}


# ─────────────────────────────────────────────────────────────
# PHASE 1 : Stocks en masse via listV2 (100 produits/appel)
# ─────────────────────────────────────────────────────────────
def _process_listv2_pages(cj_api, pid_map, seen_pids, category_id=None, label="global"):
    """
    Parcourir les pages listV2 et mettre à jour les stocks.
    Retourne (processed, updated).
    """
    updated = 0
    processed = 0
    page = 1
    max_pages = 200
    consecutive_empty = 0
    
    while page <= max_pages:
        try:
            result = cj_api.get_products_v2(page=page, page_size=100, category_id=category_id)
            stats['api_calls'] += 1
            products = result.get('products', [])
            
            if not products:
                consecutive_empty += 1
                if consecutive_empty >= 3:
                    logger.warning(f"  [{label}] 3 pages vides - attente 5 min...")
                    time.sleep(300)
                    result = cj_api.get_products_v2(page=page, page_size=100, category_id=category_id)
                    stats['api_calls'] += 1
                    products = result.get('products', [])
                    if not products:
                        break
                    else:
                        consecutive_empty = 0
                else:
                    page += 1
                    time.sleep(5)
                    continue
            else:
                consecutive_empty = 0
            
            for p in products:
                pid = str(p.get('pid', ''))
                if pid in seen_pids:
                    continue
                seen_pids.add(pid)
                processed += 1
                
                if pid in pid_map:
                    product = pid_map[pid]
                    new_stock = p.get('stock', 0)
                    new_price = p.get('price', 0)
                    
                    changed = False
                    
                    if new_stock > 0:
                        # Stock réel retourné par l'API → on met à jour
                        if product.stock != new_stock:
                            product.stock = new_stock
                            changed = True
                        product.stock_checked = True
                    else:
                        # API retourne 0 : ne pas écraser un stock par défaut (999)
                        # Sauf si le stock a déjà été vérifié avant (stock_checked=True)
                        if product.stock_checked:
                            if product.stock != 0:
                                product.stock = 0
                                changed = True
                    
                    if new_price and (not product.cost_price or product.cost_price == 0):
                        product.cost_price = new_price
                        changed = True
                    
                    if changed:
                        updated += 1
            
            db.session.commit()
            
            total_pages = result.get('total_pages', 0)
            if page % 5 == 0 or page >= total_pages:
                logger.info(f"  [{label}] Page {page}/{total_pages} | Traités: {processed} | MAJ: {updated}")
            
            if page >= total_pages:
                break
            
            page += 1
            time.sleep(1.5)
            
        except Exception as e:
            logger.error(f"  [{label}] Erreur page {page}: {e}")
            page += 1
            time.sleep(5)
    
    return processed, updated


def sync_all_stocks_batch(cj_api, app):
    """
    Récupère les stocks de TOUS les produits via listV2 (100/page).
    Stratégie : d'abord global (max 6000), puis par catégorie CJ pour le reste.
    """
    logger.info("\n" + "=" * 70)
    logger.info("📦 PHASE 1 : Synchronisation des stocks en masse (listV2)")
    logger.info("=" * 70)
    
    with app.app_context():
        from models.category import Category
        
        all_products = Product.query.filter(Product.cj_pid.isnot(None)).all()
        pid_map = {str(p.cj_pid): p for p in all_products}
        logger.info(f"  {len(pid_map)} produits CJ en base")
        
        seen_pids = set()
        total_updated = 0
        total_processed = 0
        
        # Étape 1 : Parcours global (couvre ~6000 premiers produits)
        logger.info("\n  --- Étape 1/2 : Parcours global listV2 ---")
        proc, upd = _process_listv2_pages(cj_api, pid_map, seen_pids, category_id=None, label="global")
        total_processed += proc
        total_updated += upd
        logger.info(f"  Global terminé: {proc} produits, {upd} MAJ, {len(seen_pids)} PIDs vus")
        
        # Étape 2 : Parcours par catégorie CJ pour les produits non couverts
        not_seen = len(pid_map) - len(seen_pids & set(pid_map.keys()))
        if not_seen > 0:
            logger.info(f"\n  --- Étape 2/2 : Parcours par catégorie ({not_seen} produits restants) ---")
            
            # Récupérer les catégories CJ qui ont des produits non encore vus
            categories = Category.query.filter(Category.cj_category_id.isnot(None)).all()
            cat_count = len(categories)
            
            for cat_idx, cat in enumerate(categories, 1):
                # Vérifier s'il reste des produits non vus dans cette catégorie
                cat_products = [p for p in all_products if p.category_id == cat.id and str(p.cj_pid) not in seen_pids]
                if not cat_products:
                    continue
                
                logger.info(f"  Catégorie {cat_idx}/{cat_count}: {cat.name} ({len(cat_products)} non vus)")
                proc, upd = _process_listv2_pages(cj_api, pid_map, seen_pids, category_id=cat.cj_category_id, label=cat.name[:30])
                total_processed += proc
                total_updated += upd
                
                # Vérifier si on a couvert tous les produits
                remaining = len(pid_map) - len(seen_pids & set(pid_map.keys()))
                if remaining == 0:
                    logger.info(f"  Tous les produits couverts !")
                    break
                
                time.sleep(1.5)
        
        db.session.commit()
        matched = len(seen_pids & set(pid_map.keys()))
        stats['stock_updated'] = total_updated
        logger.info(f"\n  ✅ Stocks: {total_updated} mis à jour sur {total_processed} traités")
        logger.info(f"  📊 Couverture: {matched}/{len(pid_map)} produits en base ({matched*100//len(pid_map)}%)")
        logger.info(f"  📡 Appels API: {stats['api_calls']}")
        return total_updated


# ─────────────────────────────────────────────────────────────
# PHASE 2 : Détails + Variantes séquentiel (rate limit safe)
# ─────────────────────────────────────────────────────────────
def apply_product_details(product, details):
    """Appliquer les détails récupérés à un produit."""
    if details.get('description'):
        product.description = details['description']
    
    if details.get('image'):
        img = details['image']
        if isinstance(img, str) and img.strip().startswith('['):
            try:
                parsed = json.loads(img)
                if isinstance(parsed, list) and parsed:
                    img = parsed[0]
            except (json.JSONDecodeError, ValueError):
                pass
        product.image_url = img
    
    if details.get('images') and len(details['images']) > 0:
        clean_imgs = []
        for im in details['images']:
            if isinstance(im, str) and im.strip().startswith('['):
                try:
                    parsed = json.loads(im)
                    if isinstance(parsed, list):
                        clean_imgs.extend(parsed)
                    else:
                        clean_imgs.append(im)
                except (json.JSONDecodeError, ValueError):
                    clean_imgs.append(im)
            else:
                clean_imgs.append(im)
        product.images = json.dumps(clean_imgs)
    
    if details.get('weight'):
        try:
            product.weight = float(details['weight'])
        except (ValueError, TypeError):
            pass
    
    if details.get('material'):
        product.material = details['material']
    
    if details.get('name'):
        product.name = details['name']
    
    if details.get('suggested_price'):
        product.suggested_price = details['suggested_price']
    
    if details.get('price') and not product.cost_price:
        try:
            product.cost_price = float(details['price'])
        except (ValueError, TypeError):
            pass
    
    if details.get('raw_data'):
        product.cj_raw_data = json.dumps(details['raw_data'], default=str)


def enrich_details_sequential(cj_api, app, variant_service, force=False, skip_hours=24, delay=1, **kwargs):
    """
    Enrichir les détails/variantes de tous les produits séquentiellement.
    Un appel à la fois pour respecter le rate limit CJ.
    """
    logger.info("\n" + "=" * 70)
    logger.info(f"⚡ PHASE 2 : Enrichissement détails + variantes (séquentiel, {delay}s/produit)")
    logger.info("=" * 70)
    
    with app.app_context():
        query = Product.query.filter(Product.cj_pid.isnot(None))
        
        if not force:
            cutoff = datetime.utcnow() - timedelta(hours=skip_hours)
            query = query.filter(
                db.or_(
                    Product.cj_last_sync == None,
                    Product.cj_last_sync < cutoff,
                    Product.description == None,
                    Product.description == ''
                )
            )
        
        products = query.all()
        total = len(products)
        
        if total == 0:
            logger.info("  ✅ Tous les produits sont déjà enrichis récemment")
            return
        
        logger.info(f"  {total} produits à enrichir")
        logger.info(f"  Estimation: ~{int(total * delay / 60)} minutes")
        
        total_saved = 0
        total_variants = 0
        start_time = time.time()
        
        consecutive_fails = 0
        
        for idx, product in enumerate(products, 1):
            try:
                # Appel 1: Détails produit
                details = cj_api.get_product_details(product.cj_pid)
                stats['api_calls'] += 1
                
                if details:
                    apply_product_details(product, details)
                    total_saved += 1
                    consecutive_fails = 0
                else:
                    # Rate limit probable - pause longue auto-adaptative
                    consecutive_fails += 1
                    pause = min(15 * consecutive_fails, 60)  # 15min, 30min, 45min, max 60min
                    logger.warning(f"  ⏸️ Rate limit détecté ({consecutive_fails}x) - pause {pause} min...")
                    db.session.commit()
                    time.sleep(pause * 60)
                    # Réessayer ce produit après la pause
                    details = cj_api.get_product_details(product.cj_pid)
                    stats['api_calls'] += 1
                    if details:
                        apply_product_details(product, details)
                        total_saved += 1
                        consecutive_fails = 0
                    else:
                        logger.error(f"  ❌ {product.cj_pid}: toujours bloqué après {pause} min")
                        continue
                
                time.sleep(delay)
                
                # Appel 2: Variantes
                try:
                    old_stock = product.stock
                    vr = variant_service.sync_product_variants(product.id)
                    stats['api_calls'] += 1
                    if vr.get('success'):
                        total_variants += vr.get('total_variants', 0)
                        variant_stock = product.calculate_total_stock_from_variants()
                        if variant_stock > 0:
                            product.stock = variant_stock
                            product.stock_checked = True
                        else:
                            # Variantes retournent 0 : garder le stock existant (999 ou listV2)
                            product.stock = old_stock
                except Exception as e:
                    logger.debug(f"Variantes {product.cj_pid}: {e}")
                
                product.cj_last_sync = datetime.utcnow()
                
                # Commit par batch de 20
                if idx % 20 == 0:
                    db.session.commit()
                
                time.sleep(delay)
                
            except Exception as e:
                logger.error(f"  ❌ {product.cj_pid}: {e}")
                stats['errors'] += 1
                db.session.rollback()
            
            # Progression tous les 20 produits
            if idx % 20 == 0:
                elapsed = time.time() - start_time
                rate = idx / elapsed if elapsed > 0 else 0
                remaining = total - idx
                eta = int(remaining / rate) if rate > 0 else 0
                
                logger.info(
                    f"  📊 {idx}/{total} | "
                    f"Détails: {total_saved} | Variantes: {total_variants} | "
                    f"Erreurs: {stats['errors']} | "
                    f"ETA: {eta // 60}min{eta % 60:02d}s"
                )
        
        db.session.commit()
        stats['details_updated'] = total_saved
        stats['variants_synced'] = total_variants
        
        logger.info(f"\n  ✅ Détails: {total_saved} enrichis | Variantes: {total_variants}")


# ─────────────────────────────────────────────────────────────
# PHASE 3 : Avis clients (optionnel, plus lent)
# ─────────────────────────────────────────────────────────────
def sync_ratings(cj_api, cj_sync, app, force=False):
    """
    Synchroniser les avis clients. Plus lent car 1 appel/produit.
    Ne traite que les produits sans avis sauf si --force.
    """
    logger.info("\n" + "=" * 70)
    logger.info("⭐ PHASE 3 : Synchronisation des avis clients")
    logger.info("=" * 70)
    
    with app.app_context():
        query = Product.query.filter(Product.cj_pid.isnot(None))
        
        if not force:
            query = query.filter(
                db.or_(
                    Product.rating_count == None,
                    Product.rating_count == 0
                )
            )
        
        products = query.all()
        total = len(products)
        
        if total == 0:
            logger.info("  ✅ Tous les produits ont déjà des avis")
            return
        
        logger.info(f"  {total} produits sans avis à traiter")
        
        updated = 0
        for idx, product in enumerate(products, 1):
            try:
                result = cj_sync.enrich_product(product.cj_pid)
                stats['api_calls'] += 1
                if result.get('success') and result.get('review_count', 0) > 0:
                    updated += 1
            except Exception as e:
                logger.debug(f"Avis {product.cj_pid}: {e}")
            
            if idx % 50 == 0:
                db.session.commit()
                logger.info(f"  📊 {idx}/{total} | Avis trouvés: {updated}")
            
            time.sleep(0.8)
        
        db.session.commit()
        stats['ratings_updated'] = updated
        logger.info(f"\n  ✅ Avis: {updated} produits avec avis trouvés")


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description='Enrichissement rapide des produits CJ')
    parser.add_argument('--force', action='store_true', help='Forcer même si déjà enrichi')
    parser.add_argument('--stock-only', action='store_true', help='Seulement les stocks (très rapide)')
    parser.add_argument('--skip-stocks', action='store_true', help='Passer la Phase 1 stocks (si déjà faite)')
    parser.add_argument('--no-ratings', action='store_true', help='Passer les avis clients')
    parser.add_argument('--workers', type=int, default=3, help='Nombre de threads parallèles (défaut: 3)')
    parser.add_argument('--skip-hours', type=int, default=24, help='Skip produits enrichis il y a moins de N heures (défaut: 24)')
    parser.add_argument('--wait', type=int, default=0, help='Attendre N minutes avant de commencer (laisser le rate limit se lever)')
    args = parser.parse_args()
    
    logger.info("=" * 70)
    logger.info("🚀 ENRICHISSEMENT RAPIDE - TOUS LES PRODUITS CJ")
    logger.info("=" * 70)
    logger.info(f"  Mode: {'stock-only' if args.stock_only else 'complet'}")
    logger.info(f"  Force: {args.force}")
    logger.info(f"  Workers: {args.workers}")
    logger.info(f"  Skip si enrichi < {args.skip_hours}h")
    
    # Attente initiale si demandée (pour laisser le rate limit se lever)
    if args.wait > 0:
        logger.info(f"\n⏳ Attente initiale de {args.wait} min avant de toucher l'API CJ...")
        for remaining in range(args.wait, 0, -1):
            if remaining % 10 == 0 or remaining <= 5:
                logger.info(f"  ... {remaining} min restantes")
            time.sleep(60)
        logger.info("  ✅ Attente terminée, démarrage !")
    
    app = create_app()
    start_time = time.time()
    
    # Initialiser l'API CJ
    cj_api = CJDropshippingApiOptimized(
        email=Config.CJ_EMAIL,
        password=Config.CJ_PASSWORD,
        dev_key=Config.CJ_DEV_KEY
    )
    
    # PHASE 1 : Stocks en masse
    if not args.skip_stocks:
        sync_all_stocks_batch(cj_api, app)
    else:
        logger.info("\n⏭️ Phase 1 stocks ignorée (--skip-stocks)")
    
    if not args.stock_only:
        # Pause entre phases seulement si Phase 1 a été exécutée
        if not args.skip_stocks:
            logger.info("\n⏳ Pause 5 min entre Phase 1 et Phase 2 (rate limit CJ)...")
            time.sleep(300)
        
        # PHASE 2 : Détails + Variantes séquentiel (rate limit safe)
        with app.app_context():
            cj_sync = CjSyncService(cj_api)
            variant_service = CjVariantSyncService(cj_api)
        
        enrich_details_sequential(
            cj_api, app, variant_service,
            force=args.force,
            skip_hours=args.skip_hours
        )
        
        # PHASE 3 : Avis clients
        if not args.no_ratings:
            with app.app_context():
                cj_sync = CjSyncService(cj_api)
            sync_ratings(cj_api, cj_sync, app, force=args.force)
    
    # Résumé final
    elapsed = time.time() - start_time
    
    logger.info("\n" + "=" * 70)
    logger.info("✅ ENRICHISSEMENT TERMINÉ")
    logger.info("=" * 70)
    logger.info(f"  Stocks mis à jour:       {stats['stock_updated']}")
    logger.info(f"  Détails enrichis:        {stats['details_updated']}")
    logger.info(f"  Variantes synchronisées: {stats['variants_synced']}")
    logger.info(f"  Avis récupérés:          {stats['ratings_updated']}")
    logger.info(f"  Erreurs:                 {stats['errors']}")
    logger.info(f"  Appels API total:        {stats['api_calls']}")
    logger.info(f"  Durée totale:            {int(elapsed // 60)}min {int(elapsed % 60)}s")
    logger.info("=" * 70)
    
    # Stats finales BDD
    with app.app_context():
        total_products = Product.query.filter(Product.cj_pid.isnot(None)).count()
        with_stock = Product.query.filter(Product.cj_pid.isnot(None), Product.stock > 0).count()
        with_desc = Product.query.filter(Product.cj_pid.isnot(None), Product.description.isnot(None), Product.description != '').count()
        with_variants = db.session.query(ProductVariant.product_id).distinct().count()
        with_ratings = Product.query.filter(Product.cj_pid.isnot(None), Product.rating_count > 0).count()
        
        logger.info(f"\n📊 ÉTAT DE LA BASE:")
        logger.info(f"  Produits CJ:        {total_products}")
        logger.info(f"  Avec stock > 0:     {with_stock} ({with_stock*100//max(total_products,1)}%)")
        logger.info(f"  Avec description:   {with_desc} ({with_desc*100//max(total_products,1)}%)")
        logger.info(f"  Avec variantes:     {with_variants} ({with_variants*100//max(total_products,1)}%)")
        logger.info(f"  Avec avis:          {with_ratings} ({with_ratings*100//max(total_products,1)}%)")
    
    return 0


if __name__ == '__main__':
    exit(main())
