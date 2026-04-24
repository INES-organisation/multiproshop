"""
Script pour mettre à jour tous les stocks des produits depuis leurs variantes
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app
from extensions import db
from models.product import Product
from models.product_variant import ProductVariant
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    logger.info("=" * 80)
    logger.info("🔄 MISE À JOUR DES STOCKS DEPUIS LES VARIANTES")
    logger.info("=" * 80)
    
    app = create_app()
    
    with app.app_context():
        try:
            # Trouver tous les produits avec variantes
            products_with_variants = db.session.query(Product).filter(
                Product.cj_pid.isnot(None),
                Product.id.in_(
                    db.session.query(ProductVariant.product_id).distinct()
                )
            ).all()
            
            total = len(products_with_variants)
            logger.info(f"\n📦 {total} produits avec variantes trouvés")
            
            updated = 0
            total_stock = 0
            
            logger.info("\n🔄 Mise à jour des stocks...")
            
            for idx, product in enumerate(products_with_variants, 1):
                old_stock = product.stock
                
                # Mettre à jour le stock depuis les variantes
                if product.update_stock_from_variants():
                    updated += 1
                    total_stock += product.stock
                
                if idx % 100 == 0:
                    logger.info(f"  Traité: {idx}/{total} | Mis à jour: {updated}")
            
            # Sauvegarder
            db.session.commit()
            
            # Statistiques finales
            products_in_stock = Product.query.filter(
                Product.cj_pid.isnot(None),
                Product.stock > 0
            ).count()
            
            logger.info("\n" + "=" * 80)
            logger.info("✅ MISE À JOUR TERMINÉE")
            logger.info("=" * 80)
            logger.info(f"  Produits traités: {total}")
            logger.info(f"  Stocks mis à jour: {updated}")
            logger.info(f"  Stock total: {total_stock}")
            logger.info(f"  Produits en stock: {products_in_stock}")
            logger.info("=" * 80)
            
            logger.info("\n💡 Vider le cache:")
            logger.info("  python scripts\\clear_cache_and_enrich.py")
            
            return 0
            
        except Exception as e:
            logger.error(f"❌ Erreur: {e}")
            import traceback
            traceback.print_exc()
            return 1


if __name__ == '__main__':
    exit(main())
