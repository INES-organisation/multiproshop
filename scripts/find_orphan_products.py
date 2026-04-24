"""
Trouver tous les produits CJ dont la catégorie CJ originale n'est pas en BDD
et analyser leur nom pour déterminer la bonne catégorie MPS.
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
    
    orphans = []
    no_cat_id = []
    
    for p in products:
        if not p.cj_raw_data:
            continue
        try:
            raw = json.loads(p.cj_raw_data)
        except:
            continue
        
        cj_cat_id = str(raw.get('categoryId') or raw.get('category_id') or '')
        
        if not cj_cat_id:
            no_cat_id.append(p)
            continue
        
        cj_cat = Category.query.filter_by(cj_category_id=cj_cat_id).first()
        if not cj_cat:
            cat_name = raw.get('categoryName', 'INCONNU')
            current_cat = Category.query.get(p.category_id) if p.category_id else None
            orphans.append({
                'id': p.id,
                'name': p.name[:70],
                'cj_cat_id': cj_cat_id,
                'cj_cat_name': cat_name,
                'current_mps': current_cat.name if current_cat else 'AUCUNE',
                'current_mps_id': p.category_id,
            })
    
    print(f"\n{'='*100}")
    print(f"PRODUITS ORPHELINS (catégorie CJ non trouvée en BDD): {len(orphans)}")
    print(f"{'='*100}\n")
    
    # Grouper par categoryName CJ
    by_cj_name = {}
    for o in orphans:
        key = o['cj_cat_name']
        if key not in by_cj_name:
            by_cj_name[key] = []
        by_cj_name[key].append(o)
    
    for cj_name, items in sorted(by_cj_name.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"\nCJ Category: {cj_name} ({len(items)} produits)")
        print(f"  CJ ID: {items[0]['cj_cat_id']}")
        print(f"  Actuellement dans: {items[0]['current_mps']}")
        for item in items[:3]:
            print(f"  Ex: {item['name']}")
    
    if no_cat_id:
        print(f"\n\nProduits sans categoryId dans raw_data: {len(no_cat_id)}")
        for p in no_cat_id[:5]:
            print(f"  ID:{p.id} - {p.name[:60]}")
