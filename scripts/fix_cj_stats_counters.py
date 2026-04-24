"""
Script pour corriger les compteurs de la page /admin/cj/products
Met à jour les compteurs de catégories et rafraîchit les statistiques
"""
import sys
import os
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app
from extensions import db
from models.product import Product
from models.product_variant import ProductVariant
from models.category import Category
from sqlalchemy import func
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def update_category_counts():
    """Mettre à jour les compteurs de produits pour toutes les catégories CJ"""
    try:
        logger.info("🔄 Mise à jour des compteurs de catégories...")
        
        # Récupérer toutes les catégories CJ
        categories = Category.query.filter(
            Category.cj_category_id.isnot(None)
        ).all()
        
        updated = 0
        
        for category in categories:
            # Compter les produits directs de cette catégorie
            direct_count = Product.query.filter(
                Product.category_id == category.id,
                Product.cj_pid.isnot(None),
                Product.published == True
            ).count()
            
            # Pour les catégories de niveau 1 et 2, inclure les sous-catégories
            total_count = direct_count
            
            if category.level == 1:
                # Ajouter produits des catégories niveau 2
                level2_cats = Category.query.filter_by(parent_id=category.id).all()
                for cat2 in level2_cats:
                    total_count += Product.query.filter(
                        Product.category_id == cat2.id,
                        Product.cj_pid.isnot(None),
                        Product.published == True
                    ).count()
                    
                    # Ajouter produits des catégories niveau 3
                    level3_cats = Category.query.filter_by(parent_id=cat2.id).all()
                    for cat3 in level3_cats:
                        total_count += Product.query.filter(
                            Product.category_id == cat3.id,
                            Product.cj_pid.isnot(None),
                            Product.published == True
                        ).count()
            
            elif category.level == 2:
                # Ajouter produits des catégories niveau 3
                level3_cats = Category.query.filter_by(parent_id=category.id).all()
                for cat3 in level3_cats:
                    total_count += Product.query.filter(
                        Product.category_id == cat3.id,
                        Product.cj_pid.isnot(None),
                        Product.published == True
                    ).count()
            
            # Mettre à jour le compteur
            if category.product_count != total_count:
                category.product_count = total_count
                updated += 1
        
        db.session.commit()
        logger.info(f"✅ {updated} catégories mises à jour")
        
        return updated
        
    except Exception as e:
        logger.error(f"❌ Erreur update_category_counts: {e}")
        db.session.rollback()
        return 0


def display_stats():
    """Afficher les statistiques actuelles"""
    try:
        logger.info("\n📊 STATISTIQUES ACTUELLES")
        logger.info("=" * 80)
        
        # Produits
        total_products = Product.query.filter(Product.cj_pid.isnot(None)).count()
        published_products = Product.query.filter(
            Product.cj_pid.isnot(None),
            Product.published == True
        ).count()
        in_stock = Product.query.filter(
            Product.cj_pid.isnot(None),
            Product.stock > 0
        ).count()
        
        logger.info(f"📦 Produits CJ:")
        logger.info(f"  - Total: {total_products}")
        logger.info(f"  - Publiés: {published_products}")
        logger.info(f"  - En stock: {in_stock}")
        
        # Variantes
        total_variants = ProductVariant.query.count()
        active_variants = ProductVariant.query.filter_by(active=True).count()
        
        logger.info(f"\n🎨 Variantes:")
        logger.info(f"  - Total: {total_variants}")
        logger.info(f"  - Actives: {active_variants}")
        
        # Catégories
        total_categories = Category.query.filter(Category.cj_category_id.isnot(None)).count()
        level1 = Category.query.filter_by(level=1).count()
        level2 = Category.query.filter_by(level=2).count()
        level3 = Category.query.filter_by(level=3).count()
        
        logger.info(f"\n📁 Catégories CJ:")
        logger.info(f"  - Total: {total_categories}")
        logger.info(f"  - Niveau 1: {level1}")
        logger.info(f"  - Niveau 2: {level2}")
        logger.info(f"  - Niveau 3: {level3}")
        
        # Produits sans variantes
        products_without_variants = db.session.query(Product).filter(
            Product.cj_pid.isnot(None),
            Product.published == True,
            ~Product.id.in_(
                db.session.query(ProductVariant.product_id).distinct()
            )
        ).count()
        
        logger.info(f"\n⚠️  Produits sans variantes: {products_without_variants}")
        
        if products_without_variants > 0:
            logger.info(f"💡 Ces produits doivent être enrichis par les workers Celery")
        
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"❌ Erreur display_stats: {e}")


def main():
    """Fonction principale"""
    logger.info("=" * 80)
    logger.info("🔧 CORRECTION DES COMPTEURS CJ")
    logger.info("=" * 80)
    
    app = create_app()
    
    with app.app_context():
        try:
            # 1. Afficher les stats avant
            logger.info("\n📊 AVANT CORRECTION")
            display_stats()
            
            # 2. Mettre à jour les compteurs
            logger.info("\n🔄 MISE À JOUR DES COMPTEURS")
            logger.info("-" * 80)
            updated = update_category_counts()
            
            # 3. Afficher les stats après
            logger.info("\n📊 APRÈS CORRECTION")
            display_stats()
            
            # 4. Résumé
            logger.info("\n" + "=" * 80)
            logger.info("✅ CORRECTION TERMINÉE")
            logger.info("=" * 80)
            logger.info(f"  {updated} catégories mises à jour")
            logger.info("\n💡 Les compteurs sont maintenant à jour sur http://multiproshop.local/admin/cj/products")
            logger.info("=" * 80)
            
            return 0
            
        except Exception as e:
            logger.error(f"❌ Erreur fatale: {e}")
            import traceback
            traceback.print_exc()
            return 1


if __name__ == '__main__':
    exit(main())
