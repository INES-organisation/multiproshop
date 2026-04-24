"""
Masquer les catégories L1 sans produits et nettoyer les sous-catégories vides pré-existantes.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.product import Product
from models.category import Category
from extensions import db

app = create_app()

def count_products_recursive(cat_id):
    """Compte les produits dans une catégorie et toutes ses sous-catégories"""
    total = Product.query.filter_by(category_id=cat_id).count()
    children = Category.query.filter_by(parent_id=cat_id).all()
    for child in children:
        total += count_products_recursive(child.id)
    return total

with app.app_context():
    # 1. Masquer les catégories L1 vides
    print("--- 1. Catégories L1 sans produits ---\n")
    
    mps_l1 = Category.query.filter_by(level=1, is_active=True).filter(
        Category.cj_category_id.is_(None)
    ).all()
    
    hidden = 0
    for l1 in mps_l1:
        total = count_products_recursive(l1.id)
        if total == 0:
            l1.visible = False
            print(f"  Masquée: {l1.name} (0 produits)")
            hidden += 1
        else:
            print(f"  OK: {l1.name} ({total} produits)")
    
    db.session.commit()
    print(f"\n  Masquées: {hidden}")
    
    # 2. Masquer les sous-catégories L2 vides pré-existantes (pas les nouvelles CJ)
    print("\n--- 2. Sous-catégories L2 vides ---\n")
    
    mps_l2 = Category.query.filter_by(level=2, is_active=True).filter(
        Category.cj_category_id.is_(None)
    ).all()
    
    hidden_l2 = 0
    for l2 in mps_l2:
        total = count_products_recursive(l2.id)
        if total == 0:
            l2.visible = False
            hidden_l2 += 1
    
    db.session.commit()
    print(f"  Sous-catégories L2 masquées: {hidden_l2}")
    
    # 3. Masquer les sous-catégories L3 vides
    mps_l3 = Category.query.filter_by(level=3, is_active=True).filter(
        Category.cj_category_id.is_(None)
    ).all()
    
    hidden_l3 = 0
    for l3 in mps_l3:
        total = Product.query.filter_by(category_id=l3.id).count()
        if total == 0:
            l3.visible = False
            hidden_l3 += 1
    
    db.session.commit()
    print(f"  Sous-catégories L3 masquées: {hidden_l3}")
    
    # 4. Résumé final
    print(f"\n--- Résumé ---\n")
    
    visible_l1 = Category.query.filter_by(level=1, is_active=True, visible=True).filter(
        Category.cj_category_id.is_(None)
    ).order_by(Category.name).all()
    
    print(f"Catégories L1 visibles: {len(visible_l1)}")
    for l1 in visible_l1:
        total = count_products_recursive(l1.id)
        
        visible_l2 = Category.query.filter_by(
            parent_id=l1.id, level=2, is_active=True, visible=True
        ).filter(Category.cj_category_id.is_(None)).count()
        
        print(f"  {l1.name:<35} : {total:>6} produits, {visible_l2} sous-catégories")
