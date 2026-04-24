"""
Mettre à jour les compteurs de produits pour toutes les catégories CJ
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from app import create_app
from models.product import Product
from models.category import Category
from extensions import db

app = create_app()

with app.app_context():
    print("\n" + "="*70)
    print("MISE À JOUR DES COMPTEURS DE PRODUITS")
    print("="*70 + "\n")
    
    # Récupérer toutes les catégories CJ
    cj_categories = Category.query.filter(
        Category.cj_category_id.isnot(None)
    ).all()
    
    print(f"Total catégories CJ: {len(cj_categories)}")
    print("\nMise à jour des compteurs...\n")
    
    updated = 0
    categories_with_products = []
    
    for cat in cj_categories:
        # Compter les produits CJ dans cette catégorie
        count = Product.query.filter(
            Product.category_id == cat.id,
            Product.cj_pid.isnot(None)
        ).count()
        
        # Mettre à jour le compteur
        if cat.product_count != count:
            cat.product_count = count
            updated += 1
        
        if count > 0:
            categories_with_products.append({
                'name': cat.name,
                'level': cat.level,
                'count': count,
                'cj_id': cat.cj_category_id
            })
    
    # Commit les changements
    db.session.commit()
    
    print(f"✓ {updated} catégories mises à jour")
    print(f"✓ {len(categories_with_products)} catégories avec produits CJ\n")
    
    # Afficher les catégories avec produits
    print("Catégories CJ avec produits:")
    for item in sorted(categories_with_products, key=lambda x: x['count'], reverse=True):
        print(f"  - {item['name']} (Niveau {item['level']}): {item['count']} produits")
        print(f"    CJ ID: {item['cj_id']}")
    
    print("\n" + "="*70 + "\n")
