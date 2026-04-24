"""Vérifier combien de sous-catégories visibles par L1"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import create_app
from models.category import Category
app = create_app()

with app.app_context():
    l1s = Category.query.filter_by(level=1, is_active=True, visible=True).filter(
        Category.cj_category_id.is_(None)
    ).order_by(Category.name).all()
    
    total_l2 = 0
    total_l3 = 0
    for l1 in l1s:
        l2s = Category.query.filter_by(parent_id=l1.id, is_active=True, visible=True).all()
        l3_count = 0
        for l2 in l2s:
            l3_count += Category.query.filter_by(parent_id=l2.id, is_active=True, visible=True).count()
        total_l2 += len(l2s)
        total_l3 += l3_count
        print(f"  {l1.name:<35}: {len(l2s):>3} L2, {l3_count:>3} L3")
    
    print(f"\n  TOTAL: {total_l2} L2, {total_l3} L3")
