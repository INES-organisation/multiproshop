"""
Script pour mettre à jour TOUS les stocks des produits depuis leurs variantes
Puis relancer l'enrichissement pour récupérer les stocks manquants
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
    logger.info("🔄 MISE À JOUR COMPLÈTE DES STOCKS")
    logger.info("=" * 80)
    
    app = create_app()
    
    with app.app_context():
        try:
            # 1. Mettre à jour les stocks depuis les variantes existantes
            logger.info("\n📦 ÉTAPE 1: Mise à jour stocks depuis variantes existantes")
            logger.info("-" * 80)
            
            products_with_variants = db.session.query(Product).filter(
                Product.cj_pid.isnot(None),
                Product.id.in_(
                    db.session.query(ProductVariant.product_id).distinct()
                )
            ).all()
            
            updated = 0
            for product in products_with_variants:
                if product.update_stock_from_variants():
                    updated += 1
            
            db.session.commit()
            logger.info(f"✅ {updated} produits mis à jour depuis variantes existantes")
            
            # 2. Statistiques
            logger.info("\n📊 STATISTIQUES ACTUELLES")
            logger.info("-" * 80)
            
            total_products = Product.query.filter(Product.cj_pid.isnot(None)).count()
            total_variants = ProductVariant.query.count()
            products_in_stock = Product.query.filter(
                Product.cj_pid.isnot(None),
                Product.stock > 0
            ).count()
            
            # Vérifier combien de variantes ont du stock
            variants_with_stock = ProductVariant.query.filter(ProductVariant.stock > 0).count()
            
            logger.info(f"  Produits CJ: {total_products}")
            logger.info(f"  Variantes totales: {total_variants}")
            logger.info(f"  Variantes avec stock: {variants_with_stock}")
            logger.info(f"  Produits en stock: {products_in_stock}")
            
            # 3. Analyser le problème
            if variants_with_stock == 0 and total_variants > 0:
                logger.warning("\n⚠️ PROBLÈME DÉTECTÉ:")
                logger.warning(f"  {total_variants} variantes créées mais AUCUNE n'a de stock!")
                logger.warning("  Les variantes ont été créées sans récupérer leur stock depuis l'API CJ")
                logger.warning("\n💡 SOLUTION:")
                logger.warning("  Relancez l'enrichissement avec le service corrigé:")
                logger.warning("  python scripts\\full_enrich_all_products.py")
            elif products_in_stock > 0:
                logger.info(f"\n✅ {products_in_stock} produits ont du stock disponible")
            
            logger.info("\n" + "=" * 80)
            logger.info("✅ ANALYSE TERMINÉE")
            logger.info("=" * 80)
            
            return 0
            
        except Exception as e:
            logger.error(f"❌ Erreur: {e}")
            import traceback
            traceback.print_exc()
            return 1


if __name__ == '__main__':
    exit(main())
