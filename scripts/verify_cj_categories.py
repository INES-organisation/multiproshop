"""
Vérifier que les catégories affichées proviennent bien de l'API CJ officielle
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from app import create_app
from models.category import Category
from models.product import Product
from extensions import db

app = create_app()

with app.app_context():
    print("\n" + "="*70)
    print("VÉRIFICATION CATÉGORIES CJ OFFICIELLES")
    print("="*70 + "\n")
    
    # 1. Compter les catégories
    total_categories = Category.query.count()
    cj_categories = Category.query.filter(Category.cj_category_id.isnot(None)).count()
    non_cj_categories = Category.query.filter(Category.cj_category_id.is_(None)).count()
    
    print(f"Total catégories: {total_categories}")
    print(f"  - Catégories CJ (avec cj_category_id): {cj_categories}")
    print(f"  - Catégories non-CJ (sans cj_category_id): {non_cj_categories}")
    
    # 2. Vérifier les catégories visibles
    print("\n" + "-"*70)
    print("CATÉGORIES VISIBLES")
    print("-"*70)
    
    visible_cj = Category.query.filter(
        Category.cj_category_id.isnot(None),
        Category.visible == True
    ).count()
    
    visible_non_cj = Category.query.filter(
        Category.cj_category_id.is_(None),
        Category.visible == True
    ).count()
    
    print(f"Catégories visibles CJ: {visible_cj}")
    print(f"Catégories visibles non-CJ: {visible_non_cj}")
    
    # 3. Exemples de catégories CJ niveau 1
    print("\n" + "-"*70)
    print("EXEMPLES CATÉGORIES CJ NIVEAU 1")
    print("-"*70)
    
    level1_cj = Category.query.filter(
        Category.cj_category_id.isnot(None),
        Category.level == 1
    ).limit(10).all()
    
    for cat in level1_cj:
        print(f"\n{cat.name}")
        print(f"  CJ ID: {cat.cj_category_id}")
        print(f"  Visible: {cat.visible}")
        print(f"  Product count: {cat.product_count}")
    
    # 4. Vérifier les doublons (catégories avec même nom mais différents cj_category_id)
    print("\n" + "-"*70)
    print("VÉRIFICATION DOUBLONS")
    print("-"*70)
    
    # Trouver les noms de catégories qui existent en double
    from sqlalchemy import func
    duplicates = db.session.query(
        Category.name,
        func.count(Category.id).label('count')
    ).group_by(Category.name).having(func.count(Category.id) > 1).all()
    
    print(f"\nNoms de catégories en double: {len(duplicates)}")
    
    if duplicates:
        print("\nExemples (10 premiers):")
        for name, count in duplicates[:10]:
            cats = Category.query.filter_by(name=name).all()
            print(f"\n{name} ({count} occurrences):")
            for cat in cats:
                cj_marker = "CJ" if cat.cj_category_id else "Local"
                print(f"  - {cj_marker} | ID: {cat.id} | CJ ID: {cat.cj_category_id} | Products: {cat.product_count}")
    
    # 5. Produits dans catégories CJ vs non-CJ
    print("\n" + "-"*70)
    print("PRODUITS PAR TYPE DE CATÉGORIE")
    print("-"*70)
    
    # Produits dans catégories CJ
    products_in_cj_cats = db.session.query(Product).join(
        Category, Product.category_id == Category.id
    ).filter(
        Category.cj_category_id.isnot(None)
    ).count()
    
    # Produits dans catégories non-CJ
    products_in_non_cj_cats = db.session.query(Product).join(
        Category, Product.category_id == Category.id
    ).filter(
        Category.cj_category_id.is_(None)
    ).count()
    
    print(f"Produits dans catégories CJ: {products_in_cj_cats}")
    print(f"Produits dans catégories non-CJ: {products_in_non_cj_cats}")
    
    # Produits CJ dans catégories non-CJ (problème!)
    cj_products_in_non_cj_cats = db.session.query(Product).join(
        Category, Product.category_id == Category.id
    ).filter(
        Product.cj_pid.isnot(None),
        Category.cj_category_id.is_(None)
    ).count()
    
    if cj_products_in_non_cj_cats > 0:
        print(f"\n⚠️  ATTENTION: {cj_products_in_non_cj_cats} produits CJ sont dans des catégories non-CJ!")
    
    print("\n" + "="*70 + "\n")
