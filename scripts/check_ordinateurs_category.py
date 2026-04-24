"""
Script pour analyser les produits dans la catégorie Ordinateurs
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.product import Product
from models.category import Category

app = create_app()

with app.app_context():
    cat = Category.query.filter_by(name='Ordinateurs').first()
    
    if cat:
        prods = Product.query.filter_by(category_id=cat.id).limit(30).all()
        total = Product.query.filter_by(category_id=cat.id).count()
        
        print(f"\nCatégorie: {cat.name} (ID: {cat.id})")
        print(f"Total produits: {total}\n")
        print("="*80)
        print("EXEMPLES DE PRODUITS:")
        print("="*80)
        
        for i, p in enumerate(prods, 1):
            print(f"{i}. {p.name[:100]}")
