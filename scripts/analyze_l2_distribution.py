"""
Analyser la distribution des produits par catégorie CJ niveau 2,
groupée par catégorie CJ niveau 1, avec exemples de produits.
Objectif : identifier les sous-catégories CJ qui sont mal mappées.
"""
import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.product import Product
from models.category import Category

app = create_app()

with app.app_context():
    products = Product.query.filter(Product.cj_pid.isnot(None)).all()
    
    # Structure: { cj_l1_name: { cj_l2_name: { count, examples[], mps_actuel } } }
    distribution = {}
    
    for p in products:
        if not p.cj_raw_data:
            continue
        try:
            raw = json.loads(p.cj_raw_data)
        except:
            continue
        
        cj_cat_id = str(raw.get('categoryId') or raw.get('category_id') or '')
        if not cj_cat_id:
            continue
        
        cj_cat = Category.query.filter_by(cj_category_id=cj_cat_id).first()
        if not cj_cat:
            continue
        
        # Remonter au niveau 1
        current = cj_cat
        while current.parent and current.level > 1:
            current = current.parent
        l1_name = current.name
        
        # Remonter au niveau 2
        current2 = cj_cat
        while current2.parent and current2.level > 2:
            current2 = current2.parent
        l2_name = current2.name if current2.level == 2 else "(direct L1)"
        
        if l1_name not in distribution:
            distribution[l1_name] = {}
        if l2_name not in distribution[l1_name]:
            distribution[l1_name][l2_name] = {'count': 0, 'examples': [], 'mps_id': p.category_id}
        
        distribution[l1_name][l2_name]['count'] += 1
        if len(distribution[l1_name][l2_name]['examples']) < 3:
            distribution[l1_name][l2_name]['examples'].append(p.name[:65])
    
    # Afficher
    for l1_name in sorted(distribution.keys()):
        l2s = distribution[l1_name]
        total = sum(v['count'] for v in l2s.values())
        print(f"\n{'='*90}")
        print(f"CJ L1: {l1_name} ({total} produits)")
        print(f"{'='*90}")
        
        for l2_name, info in sorted(l2s.items(), key=lambda x: x[1]['count'], reverse=True):
            mps_cat = Category.query.get(info['mps_id'])
            mps_name = mps_cat.name if mps_cat else '?'
            print(f"\n  L2: {l2_name:<35} | {info['count']:>5} produits | MPS: {mps_name}")
            for ex in info['examples']:
                print(f"      Ex: {ex}")
