"""Vérifier l'origine CJ des produits tech dans Mode"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import create_app
from models.product import Product
from models.category import Category
from extensions import db

app = create_app()

with app.app_context():
    mode_prods = Product.query.filter_by(category_id=52).filter(Product.cj_pid.isnot(None)).all()
    
    tech_kw = ['laptop', 'computer', 'notebook', 'phone case', 'bluetooth', 
               'camera', 'drone', 'sensor', 'monitor', 'tablet stand',
               'tablet bracket', 'tablet holder']
    
    orphan_count = 0
    has_cj_count = 0
    
    for p in mode_prods:
        nl = p.name.lower()
        if not any(kw in nl for kw in tech_kw):
            continue
        
        if not p.cj_raw_data:
            orphan_count += 1
            continue
        try:
            raw = json.loads(p.cj_raw_data)
        except:
            orphan_count += 1
            continue
        
        cid = str(raw.get('categoryId', ''))
        if not cid:
            orphan_count += 1
            continue
        
        cj = Category.query.filter_by(cj_category_id=cid).first()
        if not cj:
            orphan_count += 1
        else:
            has_cj_count += 1
            if has_cj_count <= 5:
                c = cj
                while c.parent and c.level > 1:
                    c = c.parent
                print(f"  HAS CJ: {p.name[:50]} | CJ L1: {c.name} | CJ: {cj.full_path}")
    
    print(f"\nProduits tech dans Mode: {orphan_count + has_cj_count}")
    print(f"  Orphelins (CJ non trouvé): {orphan_count}")
    print(f"  Avec CJ valide: {has_cj_count}")
