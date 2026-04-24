"""
Vérifier tous les produits et leur statut CJ
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
    print("ANALYSE COMPLÈTE DES PRODUITS")
    print("="*70 + "\n")
    
    # Total produits
    total = Product.query.count()
    print(f"Total produits: {total}")
    
    # Produits avec cj_pid
    with_cj_pid = Product.query.filter(Product.cj_pid.isnot(None)).count()
    without_cj_pid = Product.query.filter(Product.cj_pid.is_(None)).count()
    
    print(f"\nProduits avec cj_pid: {with_cj_pid}")
    print(f"Produits sans cj_pid: {without_cj_pid}")
    
    # Produits actifs/publiés
    active = Product.query.filter_by(is_active=True).count()
    published = Product.query.filter_by(published=True).count()
    
    print(f"\nProduits actifs: {active}")
    print(f"Produits publiés: {published}")
    
    # Produits par catégorie CJ
    print("\nProduits dans catégories CJ:")
    products_in_cj_cat = db.session.query(Product).join(
        Category, Product.category_id == Category.id
    ).filter(
        Category.cj_category_id.isnot(None)
    ).count()
    
    print(f"  - Dans catégories CJ: {products_in_cj_cat}")
    print(f"  - Dans catégories non-CJ: {total - products_in_cj_cat}")
    
    # Exemples de produits SANS cj_pid
    print("\nExemples de produits SANS cj_pid:")
    no_pid = Product.query.filter(Product.cj_pid.is_(None)).limit(5).all()
    for p in no_pid:
        cat = Category.query.get(p.category_id) if p.category_id else None
        cat_info = f"{cat.name} (CJ: {cat.cj_category_id})" if cat else "Aucune"
        print(f"  - {p.name[:50]}...")
        print(f"    SKU: {p.sku}")
        print(f"    Catégorie: {cat_info}")
        print(f"    Active: {p.is_active}, Publiée: {p.published}")
    
    # Exemples de produits AVEC cj_pid
    print("\nExemples de produits AVEC cj_pid:")
    with_pid = Product.query.filter(Product.cj_pid.isnot(None)).limit(5).all()
    for p in with_pid:
        cat = Category.query.get(p.category_id) if p.category_id else None
        cat_info = f"{cat.name} (CJ: {cat.cj_category_id})" if cat else "Aucune"
        print(f"  - {p.name[:50]}...")
        print(f"    CJ PID: {p.cj_pid}")
        print(f"    SKU: {p.sku}")
        print(f"    Catégorie: {cat_info}")
        print(f"    Active: {p.is_active}, Publiée: {p.published}")
    
    # Vérifier les catégories
    print("\nCatégories:")
    total_cat = Category.query.count()
    cj_cat = Category.query.filter(Category.cj_category_id.isnot(None)).count()
    print(f"  - Total: {total_cat}")
    print(f"  - Catégories CJ: {cj_cat}")
    print(f"  - Catégories non-CJ: {total_cat - cj_cat}")
    
    print("\n" + "="*70 + "\n")
