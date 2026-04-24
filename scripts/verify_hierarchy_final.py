"""Vérification finale de la hiérarchie MPS 3 niveaux avec comptage produits"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.product import Product
from models.category import Category
from extensions import db
from sqlalchemy import func

app = create_app()

with app.app_context():
    # Catégories MPS L1 (les 12 principales)
    mps_l1 = Category.query.filter_by(level=1).filter(
        Category.cj_category_id.is_(None)
    ).order_by(Category.name).all()
    
    print("="*90)
    print("HIÉRARCHIE MPS COMPLÈTE (3 NIVEAUX)")
    print("="*90)
    
    grand_total = 0
    
    for l1 in mps_l1:
        # Compter les produits directement dans L1
        l1_direct = Product.query.filter_by(category_id=l1.id).filter(
            Product.cj_pid.isnot(None)
        ).count()
        
        # Compter les produits dans toutes les sous-catégories
        l2s = Category.query.filter_by(parent_id=l1.id, level=2).order_by(Category.name).all()
        l2_total = 0
        l3_total = 0
        
        for l2 in l2s:
            l2_count = Product.query.filter_by(category_id=l2.id).filter(
                Product.cj_pid.isnot(None)
            ).count()
            l2_total += l2_count
            
            l3s = Category.query.filter_by(parent_id=l2.id, level=3).all()
            for l3 in l3s:
                l3_count = Product.query.filter_by(category_id=l3.id).filter(
                    Product.cj_pid.isnot(None)
                ).count()
                l3_total += l3_count
        
        branch_total = l1_direct + l2_total + l3_total
        grand_total += branch_total
        
        print(f"\n{'─'*90}")
        print(f"  {l1.name} ({branch_total} produits) [L1 direct: {l1_direct}]")
        print(f"{'─'*90}")
        
        for l2 in l2s:
            l2_count = Product.query.filter_by(category_id=l2.id).filter(
                Product.cj_pid.isnot(None)
            ).count()
            
            l3s = Category.query.filter_by(parent_id=l2.id, level=3).order_by(Category.name).all()
            l3_sum = 0
            for l3 in l3s:
                l3_sum += Product.query.filter_by(category_id=l3.id).filter(
                    Product.cj_pid.isnot(None)
                ).count()
            
            sub = l2_count + l3_sum
            if sub > 0 or l3s:
                print(f"    ├─ {l2.name} ({sub})")
                
                for l3 in l3s:
                    l3_count = Product.query.filter_by(category_id=l3.id).filter(
                        Product.cj_pid.isnot(None)
                    ).count()
                    if l3_count > 0:
                        print(f"    │   ├─ {l3.name} ({l3_count})")
    
    print(f"\n{'='*90}")
    print(f"  GRAND TOTAL: {grand_total} produits CJ")
    print(f"{'='*90}")
    
    # Résumé
    total_l1 = len(mps_l1)
    total_l2 = Category.query.filter_by(level=2).filter(Category.cj_category_id.is_(None)).count()
    total_l3 = Category.query.filter_by(level=3).filter(Category.cj_category_id.is_(None)).count()
    
    print(f"\n  Catégories MPS L1: {total_l1}")
    print(f"  Catégories MPS L2: {total_l2}")
    print(f"  Catégories MPS L3: {total_l3}")
    print(f"  Total catégories MPS: {total_l1 + total_l2 + total_l3}")
