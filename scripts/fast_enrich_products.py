"""
Script d'enrichissement RAPIDE des produits CJ
Récupère toutes les données: description, variantes, stock, avis, livraison
Optimisé pour aller le plus vite possible sans dépasser les limites API
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app
from extensions import db
from models.product import Product
from models.product_variant import ProductVariant
from services.api_providers.cj_dropshipping_optimized import CJDropshippingApiOptimized
from services.cj_sync_service import CjSyncService
from services.cj_variant_sync_service import CjVariantSyncService
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Compteurs thread-safe
lock = threading.Lock()
stats = {
    'enriched': 0,
    'variants_synced': 0,
    'errors': 0,
    'skipped': 0
}


def get_cj_credentials():
    """Récupérer les identifiants CJ"""
    from dotenv import load_dotenv
    load_dotenv()
    
    email = os.getenv('CJ_EMAIL')
    password = os.getenv('CJ_PASSWORD')
    dev_key = os.getenv('CJ_DEV_KEY')
    
    if not email or not password:
        raise ValueError("CJ_EMAIL et CJ_PASSWORD doivent être définis dans .env")
    
    return email, password, dev_key


def enrich_single_product(product_id, cj_api, batch_num, product_num, total_in_batch):
    """Enrichir un seul produit (thread-safe)"""
    app = create_app()
    
    with app.app_context():
        try:
            product = Product.query.get(product_id)
            if not product or not product.cj_pid:
                with lock:
                    stats['skipped'] += 1
                return
            
            # Services
            cj_sync = CjSyncService(cj_api)
            variant_service = CjVariantSyncService(cj_api)
            
            # 1. Enrichir avec détails (description, avis)
            try:
                result = cj_sync.enrich_product(product.cj_pid)
                if not result.get('success'):
                    logger.warning(f"⚠️ Enrichissement partiel pour {product.cj_pid}")
            except Exception as e:
                logger.error(f"❌ Erreur enrichissement {product.cj_pid}: {e}")
            
            # 2. Synchroniser les variantes
            try:
                variant_result = variant_service.sync_product_variants(product_id)
                if variant_result.get('success'):
                    # Mettre à jour le stock principal
                    product.update_stock_from_variants()
                    db.session.commit()
                    
                    with lock:
                        stats['variants_synced'] += variant_result.get('total_variants', 0)
            except Exception as e:
                logger.warning(f"⚠️ Erreur variantes {product.cj_pid}: {e}")
            
            with lock:
                stats['enriched'] += 1
                
            # Log progression
            if stats['enriched'] % 10 == 0:
                logger.info(f"📊 Lot {batch_num}: {stats['enriched']} enrichis, {stats['variants_synced']} variantes, {stats['errors']} erreurs")
            
        except Exception as e:
            with lock:
                stats['errors'] += 1
            logger.error(f"❌ Erreur produit {product_id}: {e}")


def main():
    """Fonction principale optimisée"""
    logger.info("=" * 80)
    logger.info("⚡ ENRICHISSEMENT RAPIDE DES PRODUITS CJ")
    logger.info("=" * 80)
    
    app = create_app()
    
    with app.app_context():
        try:
            # 1. Trouver les produits à enrichir
            logger.info("\n🔍 RECHERCHE DES PRODUITS À ENRICHIR")
            logger.info("-" * 80)
            
            products_without_variants = db.session.query(Product).filter(
                Product.cj_pid.isnot(None),
                Product.published == True,
                ~Product.id.in_(
                    db.session.query(ProductVariant.product_id).distinct()
                )
            ).all()
            
            total = len(products_without_variants)
            logger.info(f"✅ {total} produits à enrichir")
            
            if total == 0:
                logger.info("\n✅ Tous les produits sont déjà enrichis !")
                return 0
            
            # 2. Initialiser l'API CJ
            logger.info("\n🔑 CONNEXION À L'API CJ")
            logger.info("-" * 80)
            email, password, dev_key = get_cj_credentials()
            cj_api = CJDropshippingApiOptimized(email, password, dev_key)
            logger.info("✅ Connexion établie")
            
            # 3. Enrichissement par lots avec threads
            logger.info("\n⚡ ENRICHISSEMENT RAPIDE")
            logger.info("-" * 80)
            logger.info(f"  Mode: Lots de 20 produits")
            logger.info(f"  Threads: 5 simultanés par lot")
            logger.info(f"  Délai entre lots: 3 secondes")
            logger.info(f"  Estimation: ~{(total * 2) // 60} minutes")
            
            batch_size = 20
            max_workers = 5  # 5 threads simultanés
            total_batches = (total + batch_size - 1) // batch_size
            
            start_time = time.time()
            
            for batch_num in range(total_batches):
                start_idx = batch_num * batch_size
                end_idx = min(start_idx + batch_size, total)
                batch = products_without_variants[start_idx:end_idx]
                
                logger.info(f"\n📦 Lot {batch_num + 1}/{total_batches} ({len(batch)} produits)")
                
                # Enrichir en parallèle avec ThreadPoolExecutor
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    futures = []
                    for idx, product in enumerate(batch):
                        future = executor.submit(
                            enrich_single_product,
                            product.id,
                            cj_api,
                            batch_num + 1,
                            idx + 1,
                            len(batch)
                        )
                        futures.append(future)
                    
                    # Attendre que tous les threads se terminent
                    for future in as_completed(futures):
                        try:
                            future.result()
                        except Exception as e:
                            logger.error(f"❌ Erreur thread: {e}")
                
                # Progression
                elapsed = time.time() - start_time
                products_done = stats['enriched'] + stats['errors'] + stats['skipped']
                if products_done > 0:
                    rate = products_done / elapsed
                    remaining = total - products_done
                    eta_seconds = remaining / rate if rate > 0 else 0
                    eta_minutes = int(eta_seconds / 60)
                    
                    logger.info(f"  ✅ {stats['enriched']} enrichis, {stats['variants_synced']} variantes")
                    logger.info(f"  ⏱️  Vitesse: {rate:.1f} produits/sec | ETA: ~{eta_minutes} min")
                
                # Délai entre les lots (sauf le dernier)
                if batch_num < total_batches - 1:
                    time.sleep(3)
            
            # 4. Résumé
            elapsed_total = time.time() - start_time
            logger.info("\n" + "=" * 80)
            logger.info("✅ ENRICHISSEMENT TERMINÉ")
            logger.info("=" * 80)
            logger.info(f"  Produits enrichis: {stats['enriched']}")
            logger.info(f"  Variantes synchronisées: {stats['variants_synced']}")
            logger.info(f"  Erreurs: {stats['errors']}")
            logger.info(f"  Ignorés: {stats['skipped']}")
            logger.info(f"  Temps total: {int(elapsed_total / 60)} min {int(elapsed_total % 60)} sec")
            logger.info(f"  Vitesse moyenne: {stats['enriched'] / elapsed_total:.1f} produits/sec")
            logger.info("=" * 80)
            
            # 5. Mettre à jour les compteurs
            logger.info("\n📊 MISE À JOUR DES COMPTEURS")
            logger.info("-" * 80)
            from services.cj_sync_service import CjSyncService
            cj_sync = CjSyncService(cj_api)
            cj_sync._update_category_counts()
            logger.info("✅ Compteurs mis à jour")
            
            logger.info("\n💡 Vérifiez les résultats sur:")
            logger.info("  http://multiproshop.local/admin/cj/products")
            
            return 0
            
        except Exception as e:
            logger.error(f"❌ Erreur fatale: {e}")
            import traceback
            traceback.print_exc()
            return 1


if __name__ == '__main__':
    exit(main())
