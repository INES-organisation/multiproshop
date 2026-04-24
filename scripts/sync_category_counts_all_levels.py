"""
Synchroniser les compteurs de produits pour TOUS les niveaux de catégories
Les catégories de niveau 1 et 2 doivent avoir la somme des produits de leurs enfants
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
    print("SYNCHRONISATION COMPTEURS - TOUS NIVEAUX")
    print("="*70 + "\n")
    
    # 1. Mettre à jour les compteurs niveau 3 (produits directs)
    print("1. NIVEAU 3 - Comptage direct des produits")
    print("-" * 70)
    
    level3_cats = Category.query.filter_by(level=3).all()
    updated_l3 = 0
    
    for cat in level3_cats:
        count = Product.query.filter(
            Product.category_id == cat.id,
            Product.is_active == True
        ).count()
        
        if cat.product_count != count:
            cat.product_count = count
            updated_l3 += 1
    
    db.session.commit()
    print(f"✓ {updated_l3} catégories niveau 3 mises à jour")
    
    # 2. Mettre à jour les compteurs niveau 2 (somme des enfants niveau 3)
    print("\n2. NIVEAU 2 - Somme des produits des enfants")
    print("-" * 70)
    
    level2_cats = Category.query.filter_by(level=2).all()
    updated_l2 = 0
    
    for cat in level2_cats:
        # Compter les produits de tous les enfants niveau 3
        children_l3 = Category.query.filter_by(parent_id=cat.id, level=3).all()
        total = sum(child.product_count for child in children_l3)
        
        if cat.product_count != total:
            cat.product_count = total
            updated_l2 += 1
    
    db.session.commit()
    print(f"✓ {updated_l2} catégories niveau 2 mises à jour")
    
    # 3. Mettre à jour les compteurs niveau 1 (somme des enfants niveau 2)
    print("\n3. NIVEAU 1 - Somme des produits des enfants")
    print("-" * 70)
    
    level1_cats = Category.query.filter_by(level=1).all()
    updated_l1 = 0
    
    for cat in level1_cats:
        # Compter les produits de tous les enfants niveau 2 et 3
        children_l2 = Category.query.filter_by(parent_id=cat.id, level=2).all()
        total = sum(child.product_count for child in children_l2)
        
        if cat.product_count != total:
            cat.product_count = total
            updated_l1 += 1
    
    db.session.commit()
    print(f"✓ {updated_l1} catégories niveau 1 mises à jour")
    
    # 4. Afficher les catégories avec produits par niveau
    print("\n4. RÉSUMÉ PAR NIVEAU")
    print("-" * 70)
    
    for level in [1, 2, 3]:
        cats_with_products = Category.query.filter(
            Category.level == level,
            Category.product_count > 0
        ).count()
        
        total_products = db.session.query(
            db.func.sum(Category.product_count)
        ).filter(Category.level == level).scalar() or 0
        
        print(f"Niveau {level}: {cats_with_products} catégories avec produits (Total: {total_products} produits)")
    
    # 5. Top catégories par niveau
    print("\n5. TOP CATÉGORIES PAR NIVEAU")
    print("-" * 70)
    
    for level in [1, 2, 3]:
        print(f"\nNiveau {level}:")
        top_cats = Category.query.filter(
            Category.level == level,
            Category.product_count > 0
        ).order_by(Category.product_count.desc()).limit(5).all()
        
        for cat in top_cats:
            cj_marker = "🔵 CJ" if cat.cj_category_id else "⚪ Local"
            print(f"  {cj_marker} {cat.name[:50]:50} : {cat.product_count:3} produits")
    
    print("\n" + "="*70 + "\n")
