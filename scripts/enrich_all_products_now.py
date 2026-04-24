"""
Script d'enrichissement MASSIF de tous les produits CJ
Récupère les variantes et met à jour le stock pour chaque produit
Version SIMPLE et RAPIDE sans threads pour éviter les erreurs
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
    'variants_created': 0,
    'errors': 0,
    'skipped': 0
}


def main():
    """Fonction principale"""
    logger.info("=" * 80)
    logger.info("⚡ ENRICHISSEMENT MASSIF DES PRODUITS CJ")
    logger.info("=" * 80)
    
    app = create_app()
    
    with app.app_context():
        try:
            # 1. Trouver les produits à enrichir
            logger.info("\n🔍 RECHERCHE DES PRODUITS À ENRICHIR")
            logger.info("-" * 80)
            
            products_without_variants = Product.query.filter(
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
            
            # 2. Initialiser l'API
            logger.info("\n🔑 CONNEXION API CJ")
            logger.info("-" * 80)
            cj_api = CJDropshippingApiOptimized(
                email=Config.CJ_EMAIL,
                password=Config.CJ_PASSWORD,
                dev_key=Config.CJ_DEV_KEY
            )
            variant_service = CjVariantSyncService(cj_api)
            logger.info("✅ Connexion établie")
            
            # 3. Enrichissement séquentiel
            logger.info("\n⚡ ENRICHISSEMENT EN COURS")
            logger.info("-" * 80)
            logger.info(f"  Mode: Séquentiel (1 par 1)")
            logger.info(f"  Délai entre produits: 1 seconde")
            logger.info(f"  Estimation: ~{(total * 1.5) // 60} minutes")
            
            start_time = time.time()
            
            for idx, product in enumerate(products_without_variants, 1):
                try:
                    # Synchroniser les variantes
                    variant_result = variant_service.sync_product_variants(product.id)
                    
                    if variant_result.get('success'):
                        stats['enriched'] += 1
                        stats['variants_created'] += variant_result.get('total_variants', 0)
                        
                        # Mettre à jour le stock
                        product.update_stock_from_variants()
                        db.session.commit()
                    else:
                        stats['skipped'] += 1
                    
                    # Afficher progression tous les 10 produits
                    if idx % 10 == 0:
                        elapsed = time.time() - start_time
                        rate = idx / elapsed if elapsed > 0 else 0
                        remaining = total - idx
                        eta_seconds = remaining / rate if rate > 0 else 0
                        eta_minutes = int(eta_seconds / 60)
                        
                        logger.info(f"📊 {idx}/{total} | Enrichis: {stats['enriched']} | Variantes: {stats['variants_created']} | ETA: ~{eta_minutes}min")
                    
                    # Délai pour respecter les limites API
                    time.sleep(1)
                    
                except Exception as e:
                    stats['errors'] += 1
                    logger.error(f"❌ Erreur produit {product.cj_pid}: {e}")
                    time.sleep(2)  # Délai plus long en cas d'erreur
            
            # 4. Résumé
            elapsed_total = time.time() - start_time
            logger.info("\n" + "=" * 80)
            logger.info("✅ ENRICHISSEMENT TERMINÉ")
            logger.info("=" * 80)
            logger.info(f"  Produits enrichis: {stats['enriched']}")
            logger.info(f"  Variantes créées: {stats['variants_created']}")
            logger.info(f"  Erreurs: {stats['errors']}")
            logger.info(f"  Ignorés: {stats['skipped']}")
            logger.info(f"  Temps total: {int(elapsed_total / 60)}min {int(elapsed_total % 60)}s")
            logger.info(f"  Vitesse moyenne: {stats['enriched'] / elapsed_total:.2f} produits/sec")
            logger.info("=" * 80)
            
            # 5. Mettre à jour les compteurs
            logger.info("\n📊 MISE À JOUR DES COMPTEURS")
            logger.info("-" * 80)
            
            # Compter les résultats
            total_variants = ProductVariant.query.count()
            products_with_stock = Product.query.filter(
                Product.cj_pid.isnot(None),
                Product.stock > 0
            ).count()
            
            logger.info(f"✅ Variantes totales: {total_variants}")
            logger.info(f"✅ Produits en stock: {products_with_stock}")
            
            logger.info("\n💡 Vérifiez les résultats sur:")
            logger.info("  http://multiproshop.local/admin/cj/products")
            logger.info("\n💡 Videz le cache avec:")
            logger.info("  python scripts\\clear_cache_and_enrich.py")
            
            return 0
            
        except Exception as e:
            logger.error(f"❌ Erreur fatale: {e}")
            import traceback
            traceback.print_exc()
            return 1


if __name__ == '__main__':
    exit(main())
