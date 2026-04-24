import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from models.category import Category

def check_remaining_cj_categories():
    """Vérifie les catégories restantes et identifie celles qui sont CJ"""
    with app.app_context():
        try:
            # Vérifier toutes les catégories
            all_categories = Category.query.all()
            print(f"Total de catégories dans la base: {len(all_categories)}")
            
            # Catégories avec cj_category_id
            cj_with_id = Category.query.filter(Category.cj_category_id.isnot(None)).all()
            print(f"\nCatégories avec cj_category_id: {len(cj_with_id)}")
            for cat in cj_with_id[:10]:
                print(f"  - {cat.name} (ID: {cat.id}, CJ ID: {cat.cj_category_id})")
            
            # Afficher quelques catégories pour analyse
            print(f"\n10 premières catégories:")
            for cat in all_categories[:10]:
                print(f"  ID: {cat.id}, Nom: {cat.name}, Slug: {cat.slug}, CJ ID: {cat.cj_category_id}, Parent: {cat.parent_id}")
            
            # Chercher des patterns dans les slugs ou noms
            print(f"\nCatégories de niveau 1:")
            level1_cats = Category.query.filter_by(level=1).all()
            for cat in level1_cats:
                print(f"  - {cat.name} (ID: {cat.id}, Slug: {cat.slug}, CJ ID: {cat.cj_category_id})")
                
        except Exception as e:
            print(f"Erreur: {str(e)}")
            raise

if __name__ == '__main__':
    check_remaining_cj_categories()
