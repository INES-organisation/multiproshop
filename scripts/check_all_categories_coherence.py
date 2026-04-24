"""
Script pour vérifier la cohérence de toutes les catégories
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.product import Product
from models.category import Category

app = create_app()

with app.app_context():
    # Catégories principales à vérifier
    categories_to_check = [
        ('Jeux & Jouets', 126),
        ('Sports & Loisirs', 100),
        ('Bébés & Puériculture', 113),
        ('Animalerie', 178),
        ('Auto & Moto', 139),
    ]
    
    print("\n" + "="*80)
    print("VÉRIFICATION DE LA COHÉRENCE DES CATÉGORIES")
    print("="*80 + "\n")
    
    for cat_name, cat_id in categories_to_check:
        cat = Category.query.get(cat_id)
        if not cat:
            continue
        
        prods = Product.query.filter_by(category_id=cat_id).limit(20).all()
        total = Product.query.filter_by(category_id=cat_id).count()
        
        print(f"\n{'='*80}")
        print(f"Catégorie: {cat_name} (ID: {cat_id})")
        print(f"Total produits: {total}")
        print(f"{'='*80}\n")
        
        for i, p in enumerate(prods, 1):
            print(f"{i}. {p.name[:100]}")
        
        print()
