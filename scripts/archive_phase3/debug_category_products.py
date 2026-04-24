"""
Débugger les produits par catégorie
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
    print("DEBUG PRODUITS PAR CATÉGORIE")
    print("="*70 + "\n")
    
    # Tester avec "Computer & Office" (catégorie niveau 1)
    cat_name = "Computer & Office"
    cat = Category.query.filter(Category.name == cat_name).first()
    
    if cat:
        print(f"Catégorie trouvée: {cat.name}")
        print(f"  ID: {cat.id}")
        print(f"  CJ ID: {cat.cj_category_id}")
        print(f"  Niveau: {cat.level}")
        print(f"  Product count: {cat.product_count}")
        
        # Produits directs dans cette catégorie
        direct_products = Product.query.filter(
            Product.category_id == cat.id,
            Product.cj_pid.isnot(None)
        ).count()
        
        print(f"\nProduits directs: {direct_products}")
        
        # Trouver toutes les sous-catégories
        if cat.level == 1:
            # Niveau 2
            level2_cats = Category.query.filter_by(parent_id=cat.id).all()
            print(f"\nSous-catégories niveau 2: {len(level2_cats)}")
            
            total_in_children = 0
            for cat2 in level2_cats:
                # Niveau 3
                level3_cats = Category.query.filter_by(parent_id=cat2.id).all()
                
                for cat3 in level3_cats:
                    count = Product.query.filter(
                        Product.category_id == cat3.id,
                        Product.cj_pid.isnot(None)
                    ).count()
                    
                    if count > 0:
                        print(f"  - {cat3.name}: {count} produits")
                        total_in_children += count
            
            print(f"\nTotal produits dans sous-catégories: {total_in_children}")
        
        # Tester avec une catégorie niveau 3 qui a des produits
        print("\n" + "-"*70)
        print("Test avec Computer Tablet Accessories (niveau 3)")
        print("-"*70)
        
        cat3 = Category.query.filter(
            Category.name == "Computer Tablet Accessories",
            Category.cj_category_id.isnot(None)
        ).first()
        
        if cat3:
            print(f"\nCatégorie: {cat3.name}")
            print(f"  ID: {cat3.id}")
            print(f"  CJ ID: {cat3.cj_category_id}")
            print(f"  Niveau: {cat3.level}")
            print(f"  Product count: {cat3.product_count}")
            
            products = Product.query.filter(
                Product.category_id == cat3.id,
                Product.cj_pid.isnot(None)
            ).limit(5).all()
            
            print(f"\nExemples de produits ({len(products)}):")
            for p in products:
                print(f"  - {p.name[:50]}")
                print(f"    CJ PID: {p.cj_pid}")
                print(f"    Actif: {p.is_active}, Publié: {p.published}")
    
    print("\n" + "="*70 + "\n")
