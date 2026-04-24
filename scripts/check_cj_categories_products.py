"""
Vérifier les catégories CJ et leurs produits
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
    print("CATÉGORIES CJ ET LEURS PRODUITS")
    print("="*70 + "\n")
    
    # Catégories CJ avec produits
    cj_categories = Category.query.filter(
        Category.cj_category_id.isnot(None)
    ).order_by(Category.level, Category.name).all()
    
    print(f"Total catégories CJ: {len(cj_categories)}\n")
    
    # Compter les produits par catégorie CJ
    categories_with_products = []
    
    for cat in cj_categories:
        # Compter les produits CJ dans cette catégorie
        product_count = Product.query.filter(
            Product.category_id == cat.id,
            Product.cj_pid.isnot(None)
        ).count()
        
        if product_count > 0:
            categories_with_products.append({
                'category': cat,
                'count': product_count
            })
    
    print(f"Catégories CJ avec produits: {len(categories_with_products)}\n")
    
    # Afficher les 20 premières catégories avec produits
    print("Top 20 catégories avec produits CJ:")
    for item in sorted(categories_with_products, key=lambda x: x['count'], reverse=True)[:20]:
        cat = item['category']
        count = item['count']
        print(f"  - {cat.name} (Niveau {cat.level}): {count} produits")
        print(f"    CJ ID: {cat.cj_category_id}")
    
    # Statistiques globales
    print(f"\n" + "="*70)
    print("STATISTIQUES GLOBALES")
    print("="*70)
    
    total_products_cj = Product.query.filter(Product.cj_pid.isnot(None)).count()
    print(f"\nTotal produits avec cj_pid: {total_products_cj}")
    
    products_in_cj_categories = db.session.query(Product).join(
        Category, Product.category_id == Category.id
    ).filter(
        Product.cj_pid.isnot(None),
        Category.cj_category_id.isnot(None)
    ).count()
    
    print(f"Produits CJ dans catégories CJ: {products_in_cj_categories}")
    print(f"Produits CJ hors catégories CJ: {total_products_cj - products_in_cj_categories}")
    
    print("\n" + "="*70 + "\n")
