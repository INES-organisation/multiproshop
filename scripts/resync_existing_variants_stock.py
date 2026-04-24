"""
Script pour RE-SYNCHRONISER les variantes existantes et récupérer leurs stocks
Utilise le service corrigé qui récupère maintenant variantStock depuis l'API CJ
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
    'processed': 0,
    'updated': 0,
    'errors': 0,
    'total_stock': 0
}


def main():
    logger.info("=" * 80)
    logger.info("🔄 RE-SYNCHRONISATION DES VARIANTES EXISTANTES")
    logger.info("=" * 80)
    
    app = create_app()
    
    with app.app_context():
        try:
            # 1. Trouver tous les produits avec variantes
            logger.info("\n🔍 RECHERCHE DES PRODUITS AVEC VARIANTES")
            logger.info("-" * 80)
            
            products_with_variants = db.session.query(Product).filter(
                Product.cj_pid.isnot(None),
                Product.id.in_(
                    db.session.query(ProductVariant.product_id).distinct()
                )
            ).all()
            
            total = len(products_with_variants)
            logger.info(f"✅ {total} produits avec variantes trouvés")
            
            # 2. Initialiser le service
            logger.info("\n🔑 INITIALISATION DU SERVICE")
            logger.info("-" * 80)
            cj_api = CJDropshippingApiOptimized(
                email=Config.CJ_EMAIL,
                password=Config.CJ_PASSWORD,
                dev_key=Config.CJ_DEV_KEY
            )
            variant_service = CjVariantSyncService(cj_api)
            logger.info("✅ Service initialisé avec correction variantStock")
            
            # 3. Re-synchroniser les variantes
            logger.info("\n⚡ RE-SYNCHRONISATION DES VARIANTES")
            logger.info("-" * 80)
            logger.info(f"  Mode: Séquentiel")
            logger.info(f"  Délai entre produits: 1.5 secondes")
            logger.info(f"  Estimation: ~{(total * 1.5) // 60} minutes")
            
            start_time = time.time()
            
            for idx, product in enumerate(products_with_variants, 1):
                try:
                    # Re-synchroniser les variantes (va mettre à jour les stocks)
                    result = variant_service.sync_product_variants(product.id)
                    
                    if result.get('success'):
                        stats['processed'] += 1
                        
                        # Mettre à jour le stock du produit principal
                        if product.update_stock_from_variants():
                            stats['updated'] += 1
                            stats['total_stock'] += product.stock
                        
                        db.session.commit()
                    else:
                        stats['errors'] += 1
                    
                    # Afficher progression tous les 10 produits
                    if idx % 10 == 0:
                        elapsed = time.time() - start_time
                        rate = idx / elapsed if elapsed > 0 else 0
                        remaining = total - idx
                        eta_seconds = remaining / rate if rate > 0 else 0
                        eta_minutes = int(eta_seconds / 60)
                        
                        logger.info(f"📊 {idx}/{total} | Traités: {stats['processed']} | Mis à jour: {stats['updated']} | Stock total: {stats['total_stock']} | ETA: ~{eta_minutes}min")
                    
                    # Délai pour respecter les limites API
                    time.sleep(1.5)
                    
                except Exception as e:
                    stats['errors'] += 1
                    logger.error(f"❌ Erreur produit {product.cj_pid}: {e}")
                    time.sleep(2)
            
            # 4. Résumé
            elapsed_total = time.time() - start_time
            
            # Statistiques finales
            products_in_stock = Product.query.filter(
                Product.cj_pid.isnot(None),
                Product.stock > 0
            ).count()
            variants_with_stock = ProductVariant.query.filter(ProductVariant.stock > 0).count()
            
            logger.info("\n" + "=" * 80)
            logger.info("✅ RE-SYNCHRONISATION TERMINÉE")
            logger.info("=" * 80)
            logger.info(f"  Produits traités: {stats['processed']}")
            logger.info(f"  Produits mis à jour: {stats['updated']}")
            logger.info(f"  Erreurs: {stats['errors']}")
            logger.info(f"  Stock total récupéré: {stats['total_stock']}")
            logger.info(f"  Temps total: {int(elapsed_total / 60)}min {int(elapsed_total % 60)}s")
            logger.info("=" * 80)
            
            logger.info("\n📊 STATISTIQUES FINALES")
            logger.info("-" * 80)
            logger.info(f"  Produits en stock: {products_in_stock}")
            logger.info(f"  Variantes avec stock: {variants_with_stock}")
            
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
