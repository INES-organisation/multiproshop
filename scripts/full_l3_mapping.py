"""
Extraire TOUTES les catégories CJ L3 réellement utilisées par les produits,
avec leur chemin L1 > L2 > L3, et le nombre de produits.
Puis proposer le mapping L3 -> MPS.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.product import Product
from models.category import Category
from extensions import db

app = create_app()

with app.app_context():
    products = Product.query.filter(Product.cj_pid.isnot(None)).all()
    
    # Collecter toutes les catégories CJ L3 utilisées
    # Structure: cj_cat_id -> { l1, l2, l3, count, examples }
    l3_data = {}
    no_cat = 0
    not_found = 0
    
    for p in products:
        if not p.cj_raw_data:
            continue
        try:
            raw = json.loads(p.cj_raw_data)
        except:
            continue
        
        cj_cat_id = str(raw.get('categoryId') or '')
        if not cj_cat_id:
            no_cat += 1
            continue
        
        cj_cat = Category.query.filter_by(cj_category_id=cj_cat_id).first()
        if not cj_cat:
            not_found += 1
            continue
        
        # Remonter la hiérarchie
        l3_name = cj_cat.name
        l3_cj_id = cj_cat.cj_category_id
        
        # Niveau 2
        cat2 = cj_cat
        while cat2.parent and cat2.level > 2:
            cat2 = cat2.parent
        l2_name = cat2.name if cat2.level == 2 else '(direct)'
        l2_cj_id = cat2.cj_category_id if cat2.level == 2 else None
        
        # Niveau 1
        cat1 = cat2
        while cat1.parent and cat1.level > 1:
            cat1 = cat1.parent
        l1_name = cat1.name
        
        key = l3_cj_id
        if key not in l3_data:
            l3_data[key] = {
                'l1': l1_name, 'l2': l2_name, 'l3': l3_name,
                'l2_cj_id': l2_cj_id,
                'count': 0, 'examples': []
            }
        l3_data[key]['count'] += 1
        if len(l3_data[key]['examples']) < 2:
            l3_data[key]['examples'].append(p.name[:60])
    
    # Trier par L1 > L2 > L3
    sorted_items = sorted(l3_data.items(), key=lambda x: (x[1]['l1'], x[1]['l2'], x[1]['l3']))
    
    print(f"Catégories CJ L3 utilisées: {len(l3_data)}")
    print(f"Produits sans categoryId: {no_cat}")
    print(f"Produits avec categoryId non trouvé: {not_found}")
    print(f"Total produits mappés: {sum(v['count'] for v in l3_data.values())}")
    
    current_l1 = None
    current_l2 = None
    
    for cj_id, info in sorted_items:
        if info['l1'] != current_l1:
            current_l1 = info['l1']
            l1_total = sum(v['count'] for v in l3_data.values() if v['l1'] == current_l1)
            print(f"\n{'='*100}")
            print(f"L1: {current_l1} ({l1_total} produits)")
            print(f"{'='*100}")
            current_l2 = None
        
        if info['l2'] != current_l2:
            current_l2 = info['l2']
            l2_total = sum(v['count'] for v in l3_data.values() if v['l1'] == current_l1 and v['l2'] == current_l2)
            print(f"\n  L2: {current_l2} ({l2_total} produits)")
        
        print(f"    L3: {info['l3']:<45} | {info['count']:>5} | CJ:{cj_id[:25]}")
        for ex in info['examples']:
            print(f"        Ex: {ex}")
