"""
Script pour diagnostiquer le problème d'affichage des produits CJ dans l'admin
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.product import Product
from models.category import Category

app = create_app()

with app.app_context():
    print("\n" + "="*80)
    print("DIAGNOSTIC PRODUITS CJ ADMIN")
    print("="*80 + "\n")
    
    # 1. Vérifier les catégories CJ
    cj_cats = Category.query.filter(Category.cj_category_id.isnot(None)).all()
    print(f"Total catégories CJ: {len(cj_cats)}")
    
    visible_cj_cats = [c for c in cj_cats if c.visible]
    print(f"Catégories CJ visibles: {len(visible_cj_cats)}")
    
    # 2. Vérifier les produits CJ
    total_cj_products = Product.query.filter(Product.cj_pid.isnot(None)).count()
    print(f"\nTotal produits CJ: {total_cj_products}")
    
    # 3. Vérifier la distribution par catégorie
    print("\n" + "="*80)
    print("DISTRIBUTION PAR CATÉGORIE CJ (Top 10)")
    print("="*80 + "\n")
    
    cat_distribution = {}
    for cat in cj_cats:
        count = Product.query.filter_by(category_id=cat.id).filter(Product.cj_pid.isnot(None)).count()
        if count > 0:
            cat_distribution[cat] = count
    
    # Trier par nombre de produits
    sorted_cats = sorted(cat_distribution.items(), key=lambda x: x[1], reverse=True)[:10]
    
    for cat, count in sorted_cats:
        print(f"{cat.name[:50]:50} | CJ ID: {cat.cj_category_id:15} | Visible: {cat.visible} | Produits: {count}")
    
    # 4. Vérifier une catégorie spécifique avec beaucoup de produits
    if sorted_cats:
        test_cat, test_count = sorted_cats[0]
        print(f"\n" + "="*80)
        print(f"TEST CATÉGORIE: {test_cat.name}")
        print("="*80 + "\n")
        print(f"ID: {test_cat.id}")
        print(f"CJ Category ID: {test_cat.cj_category_id}")
        print(f"Visible: {test_cat.visible}")
        print(f"Level: {test_cat.level}")
        print(f"Parent ID: {test_cat.parent_id}")
        print(f"Product count (attr): {test_cat.product_count}")
        print(f"Product count (réel): {test_count}")
        
        # Afficher quelques produits
        prods = Product.query.filter_by(category_id=test_cat.id).filter(Product.cj_pid.isnot(None)).limit(5).all()
        print(f"\nExemples de produits:")
        for p in prods:
            print(f"  - {p.name[:60]} (CJ PID: {p.cj_pid})")
