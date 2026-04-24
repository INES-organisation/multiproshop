"""
Vérifier l'état des produits CJ en base de données
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
    print("ÉTAT DES PRODUITS CJ")
    print("="*70 + "\n")
    
    # Compter les produits
    total_products = Product.query.count()
    cj_products = Product.query.filter(Product.cj_pid.isnot(None)).count()
    cj_active = Product.query.filter(
        Product.cj_pid.isnot(None),
        Product.is_active == True
    ).count()
    cj_published = Product.query.filter(
        Product.cj_pid.isnot(None),
        Product.published == True
    ).count()
    
    print(f"Total produits: {total_products}")
    print(f"Produits CJ: {cj_products}")
    print(f"  - Actifs (is_active=True): {cj_active}")
    print(f"  - Publiés (published=True): {cj_published}")
    print(f"  - Inactifs: {cj_products - cj_active}")
    
    # Vérifier les catégories
    print("\nProduits CJ par catégorie:")
    cj_with_category = Product.query.filter(
        Product.cj_pid.isnot(None),
        Product.category_id.isnot(None)
    ).count()
    cj_without_category = Product.query.filter(
        Product.cj_pid.isnot(None),
        Product.category_id.is_(None)
    ).count()
    
    print(f"  - Avec catégorie: {cj_with_category}")
    print(f"  - Sans catégorie: {cj_without_category}")
    
    # Exemples de produits CJ
    print("\nExemples de produits CJ:")
    examples = Product.query.filter(Product.cj_pid.isnot(None)).limit(5).all()
    for p in examples:
        cat_name = Category.query.get(p.category_id).name if p.category_id else "Aucune"
        print(f"  - {p.name[:50]}...")
        print(f"    CJ PID: {p.cj_pid}")
        print(f"    Catégorie: {cat_name} (ID: {p.category_id})")
        print(f"    Active: {p.is_active}, Publiée: {p.published}")
        print(f"    SKU: {p.sku}, Prix: {p.price}")
    
    # Vérifier si les catégories des produits CJ sont des catégories CJ
    print("\nVérification catégories:")
    products_in_cj_categories = db.session.query(Product).join(
        Category, Product.category_id == Category.id
    ).filter(
        Product.cj_pid.isnot(None),
        Category.cj_category_id.isnot(None)
    ).count()
    
    print(f"  - Produits CJ dans catégories CJ: {products_in_cj_categories}")
    print(f"  - Produits CJ dans catégories non-CJ: {cj_with_category - products_in_cj_categories}")
    
    print("\n" + "="*70 + "\n")
