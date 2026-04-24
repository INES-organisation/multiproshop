"""
Script d'enrichissement COMPLET de tous les produits CJ
Récupère TOUTES les données:
- Détails produit (description, poids, images)
- Variantes (couleurs, tailles, SKU)
- Stock par variante
- Avis clients et notes
- Prix actualisés
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
from config import Config
import logging
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

stats = {
    'enriched': 0,
    'variants_synced': 0,
    'details_updated': 0,
    'ratings_updated': 0,
    'stock_updated': 0,
    'errors': 0,
    'skipped': 0
}


def enrich_single_product_complete(product, cj_api, cj_sync, variant_service):
    """Enrichir complètement un produit avec TOUTES les données"""
    try:
        import json
        
        # 1. Récupérer les détails complets du produit (formatés par _format_product)
        details = cj_api.get_product_details(product.cj_pid)
        if details:
            # Les clés sont: name, description, image, images, weight, material, price, suggested_price, raw_data
            if details.get('name'):
                product.name = details['name']
            
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
            
            if details.get('price'):
                try:
                    if not product.cost_price:
                        product.cost_price = float(details['price'])
                except (ValueError, TypeError):
                    pass
            
            if details.get('suggested_price'):
                product.suggested_price = details['suggested_price']
            
            # Sauvegarder les données brutes pour audit
            if details.get('raw_data'):
                product.cj_raw_data = json.dumps(details['raw_data'], default=str)
            
            stats['details_updated'] += 1
        
        # 2. Récupérer les avis clients
        try:
            result = cj_sync.enrich_product(product.cj_pid)
            if result.get('success'):
                stats['ratings_updated'] += 1
        except Exception as e:
            logger.debug(f"Avis non disponibles pour {product.cj_pid}: {e}")
        
        # 3. Synchroniser les variantes et le stock
        old_stock = product.stock or 0
        try:
            variant_result = variant_service.sync_product_variants(product.id)
            if variant_result.get('success'):
                stats['variants_synced'] += variant_result.get('total_variants', 0)
                
                # Mettre à jour le stock principal depuis les variantes
                product.update_stock_from_variants()
        except Exception as e:
            logger.debug(f"Variantes non disponibles pour {product.cj_pid}: {e}")
        
        # 4. Fallback listV2 si stock toujours 0
        if (product.stock or 0) == 0:
            try:
                result_v2 = cj_api.get_products_v2(page=1, page_size=5, keyword=product.sku or product.cj_pid)
                if result_v2.get('products'):
                    for p in result_v2['products']:
                        if str(p.get('pid')) == str(product.cj_pid):
                            product.stock = p.get('stock', 0)
                            break
            except Exception as e:
                logger.debug(f"listV2 fallback échoué pour {product.cj_pid}: {e}")
        
        if (product.stock or 0) != old_stock:
            stats['stock_updated'] += 1
        
        # Sauvegarder toutes les modifications
        db.session.commit()
        stats['enriched'] += 1
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur enrichissement {product.cj_pid}: {e}")
        db.session.rollback()
        stats['errors'] += 1
        return False


def main():
    """Fonction principale"""
    logger.info("=" * 80)
    logger.info("⚡ ENRICHISSEMENT COMPLET DE TOUS LES PRODUITS CJ")
    logger.info("=" * 80)
    
    app = create_app()
    
    with app.app_context():
        try:
            # 1. Trouver les produits à enrichir
            logger.info("\n🔍 RECHERCHE DES PRODUITS À ENRICHIR")
            logger.info("-" * 80)
            
            # Tous les produits CJ actifs
            products_to_enrich = Product.query.filter(
                Product.cj_pid.isnot(None)
            ).all()
            
            total = len(products_to_enrich)
            logger.info(f"✅ {total} produits à enrichir")
            
            if total == 0:
                logger.info("\n✅ Tous les produits sont déjà enrichis !")
                return 0
            
            # 2. Initialiser les services
            logger.info("\n🔑 INITIALISATION DES SERVICES")
            logger.info("-" * 80)
            cj_api = CJDropshippingApiOptimized(
                email=Config.CJ_EMAIL,
                password=Config.CJ_PASSWORD,
                dev_key=Config.CJ_DEV_KEY
            )
            cj_sync = CjSyncService(cj_api)
            variant_service = CjVariantSyncService(cj_api)
            logger.info("✅ Services initialisés")
            
            # 3. Enrichissement complet
            logger.info("\n⚡ ENRICHISSEMENT COMPLET EN COURS")
            logger.info("-" * 80)
            logger.info(f"  Mode: Séquentiel avec toutes les données")
            logger.info(f"  Données récupérées:")
            logger.info(f"    - Détails produit (nom, description, poids, images)")
            logger.info(f"    - Variantes (couleurs, tailles, SKU)")
            logger.info(f"    - Stock par variante")
            logger.info(f"    - Avis clients et notes")
            logger.info(f"    - Prix actualisés")
            logger.info(f"  Délai entre produits: 1.5 secondes")
            logger.info(f"  Estimation: ~{(total * 1.5) // 60} minutes")
            
            start_time = time.time()
            
            for idx, product in enumerate(products_to_enrich, 1):
                # Enrichir complètement le produit
                enrich_single_product_complete(product, cj_api, cj_sync, variant_service)
                
                # Afficher progression tous les 10 produits
                if idx % 10 == 0:
                    elapsed = time.time() - start_time
                    rate = idx / elapsed if elapsed > 0 else 0
                    remaining = total - idx
                    eta_seconds = remaining / rate if rate > 0 else 0
                    eta_minutes = int(eta_seconds / 60)
                    
                    logger.info(f"📊 {idx}/{total} | Enrichis: {stats['enriched']} | Stock MAJ: {stats['stock_updated']} | Variantes: {stats['variants_synced']} | Détails: {stats['details_updated']} | ETA: ~{eta_minutes}min")
                
                # Délai pour respecter les limites API
                time.sleep(1.5)
            
            # 4. Résumé
            elapsed_total = time.time() - start_time
            logger.info("\n" + "=" * 80)
            logger.info("✅ ENRICHISSEMENT COMPLET TERMINÉ")
            logger.info("=" * 80)
            logger.info(f"  Produits enrichis: {stats['enriched']}")
            logger.info(f"  Stocks mis à jour: {stats['stock_updated']}")
            logger.info(f"  Détails mis à jour: {stats['details_updated']}")
            logger.info(f"  Variantes synchronisées: {stats['variants_synced']}")
            logger.info(f"  Avis récupérés: {stats['ratings_updated']}")
            logger.info(f"  Erreurs: {stats['errors']}")
            logger.info(f"  Ignorés: {stats['skipped']}")
            logger.info(f"  Temps total: {int(elapsed_total / 60)}min {int(elapsed_total % 60)}s")
            logger.info(f"  Vitesse moyenne: {stats['enriched'] / elapsed_total:.2f} produits/sec")
            logger.info("=" * 80)
            
            # 5. Statistiques finales
            logger.info("\n📊 STATISTIQUES FINALES")
            logger.info("-" * 80)
            
            total_products = Product.query.filter(Product.cj_pid.isnot(None)).count()
            total_variants = ProductVariant.query.count()
            products_with_stock = Product.query.filter(
                Product.cj_pid.isnot(None),
                Product.stock > 0
            ).count()
            products_with_description = Product.query.filter(
                Product.cj_pid.isnot(None),
                Product.description.isnot(None),
                Product.description != ''
            ).count()
            products_with_ratings = Product.query.filter(
                Product.cj_pid.isnot(None),
                Product.rating_count > 0
            ).count()
            
            logger.info(f"✅ Produits CJ totaux: {total_products}")
            logger.info(f"✅ Variantes totales: {total_variants}")
            logger.info(f"✅ Produits en stock: {products_with_stock}")
            logger.info(f"✅ Produits avec description: {products_with_description}")
            logger.info(f"✅ Produits avec avis: {products_with_ratings}")
            
            logger.info("\n💡 PROCHAINES ÉTAPES:")
            logger.info("  1. Vider le cache: python scripts\\clear_cache_and_enrich.py")
            logger.info("  2. Vérifier sur: http://multiproshop.local/admin/cj/products")
            
            return 0
            
        except Exception as e:
            logger.error(f"❌ Erreur fatale: {e}")
            import traceback
            traceback.print_exc()
            return 1


if __name__ == '__main__':
    exit(main())
