"""Vérifier les categoryId des orphelins dans Mode - sont-ce des IDs numériques ?"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import create_app
from models.product import Product
from models.category import Category
app = create_app()
with app.app_context():
    mode_prods = Product.query.filter_by(category_id=52).filter(Product.cj_pid.isnot(None)).all()
    tech_kw = ['laptop', 'computer', 'notebook', 'phone case', 'bluetooth', 
               'camera', 'drone', 'sensor', 'monitor', 'tablet stand',
               'tablet bracket', 'tablet holder']
    
    cat_ids_seen = {}
    for p in mode_prods:
        nl = p.name.lower()
        if not any(kw in nl for kw in tech_kw):
            continue
        if not p.cj_raw_data:
            continue
        try:
            raw = json.loads(p.cj_raw_data)
        except:
            continue
        cid = str(raw.get('categoryId', ''))
        if cid not in cat_ids_seen:
            cat_ids_seen[cid] = 0
        cat_ids_seen[cid] += 1
    
    print("categoryId values des produits tech dans Mode:")
    for cid, count in sorted(cat_ids_seen.items(), key=lambda x: x[1], reverse=True):
        is_uuid = len(cid) > 10 and '-' in cid
        is_numeric = cid.isdigit()
        print(f"  {cid:<45} | {count:>4} produits | {'UUID' if is_uuid else 'NUMERIC' if is_numeric else 'OTHER'}")
