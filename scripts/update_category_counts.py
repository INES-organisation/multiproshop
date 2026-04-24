"""
Script pour recalculer les compteurs de produits de toutes les catégories CJ
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from models.category import Category
from models.product import Product
from extensions import db

def update_category_counts():
    """Recalculer les compteurs de produits pour toutes les catégories"""
    with app.app_context():
        print("=" * 70)
        print("MISE À JOUR DES COMPTEURS DE CATÉGORIES")
        print("=" * 70)
        
        # Récupérer toutes les catégories CJ
        categories = Category.query.filter(
            Category.cj_category_id.isnot(None)
        ).order_by(Category.level, Category.name).all()
        
        print(f"\n📊 {len(categories)} catégories CJ trouvées\n")
        
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
            
            # Mettre à jour le compteur si différent
            if category.product_count != total_count:
                old_count = category.product_count
                category.product_count = total_count
                updated += 1
                
                if total_count > 0:
                    print(f"  ✓ {category.name:<40} L{category.level}: {old_count} → {total_count}")
        
        # Sauvegarder
        db.session.commit()
        
        print("\n" + "=" * 70)
        print(f"✓ {updated} catégories mises à jour")
        print("=" * 70)
        
        # Afficher le top 10 des catégories
        print("\n📊 TOP 10 CATÉGORIES PAR NOMBRE DE PRODUITS:\n")
        
        top_categories = Category.query.filter(
            Category.cj_category_id.isnot(None),
            Category.product_count > 0
        ).order_by(Category.product_count.desc()).limit(10).all()
        
        for i, cat in enumerate(top_categories, 1):
            print(f"  {i:2d}. {cat.name:<40} {cat.product_count:>4} produits (L{cat.level})")

if __name__ == '__main__':
    update_category_counts()
    print("\n✅ Mise à jour terminée!")
