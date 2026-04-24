"""Debug: pourquoi les produits tech dans Mode ne sont pas détectés comme orphelins"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import create_app
from models.product import Product
from models.category import Category
app = create_app()
with app.app_context():
    # Prendre un produit laptop dans Mode
    p = Product.query.filter_by(category_id=52).filter(
        Product.name.ilike('%laptop bracket%'),
        Product.cj_pid.isnot(None)
    ).first()
    
    if not p:
        print("Pas de produit laptop bracket dans Mode")
        p = Product.query.filter_by(category_id=52).filter(
            Product.name.ilike('%laptop%'),
            Product.cj_pid.isnot(None)
        ).first()
    
    if p:
        print(f"Produit: {p.name}")
        print(f"category_id: {p.category_id}")
        print(f"cj_raw_data exists: {p.cj_raw_data is not None}")
        print(f"cj_raw_data length: {len(p.cj_raw_data) if p.cj_raw_data else 0}")
        
        if p.cj_raw_data:
            raw = json.loads(p.cj_raw_data)
            cid_raw = raw.get('categoryId')
            print(f"categoryId raw value: {repr(cid_raw)}")
            print(f"categoryId type: {type(cid_raw)}")
            cid = str(cid_raw or '')
            print(f"cid after str(): {repr(cid)}")
            print(f"bool(cid): {bool(cid)}")
            
            if cid:
                cj = Category.query.filter_by(cj_category_id=cid).first()
                print(f"CJ cat found: {cj is not None}")
                if cj:
                    print(f"CJ cat: {cj.full_path}")
        
        # Aussi vérifier category_id dans raw_data
        if p.cj_raw_data:
            raw = json.loads(p.cj_raw_data)
            print(f"\nAll keys with 'cat': {[k for k in raw.keys() if 'cat' in k.lower()]}")
            print(f"categoryId: {repr(raw.get('categoryId'))}")
            print(f"category_id: {repr(raw.get('category_id'))}")
    
    # Compter combien de produits CJ dans Mode ont categoryId vide vs non-vide
    mode_cj = Product.query.filter_by(category_id=52).filter(Product.cj_pid.isnot(None)).all()
    empty = 0
    non_empty = 0
    no_raw = 0
    found = 0
    not_found = 0
    
    for p2 in mode_cj:
        if not p2.cj_raw_data:
            no_raw += 1
            continue
        raw = json.loads(p2.cj_raw_data)
        cid = raw.get('categoryId')
        if not cid:
            empty += 1
        else:
            non_empty += 1
            cj = Category.query.filter_by(cj_category_id=str(cid)).first()
            if cj:
                found += 1
            else:
                not_found += 1
    
    print(f"\n=== Mode & Vêtements ({len(mode_cj)} produits CJ) ===")
    print(f"  Sans raw_data: {no_raw}")
    print(f"  categoryId vide/None: {empty}")
    print(f"  categoryId non-vide: {non_empty}")
    print(f"    -> CJ trouvé: {found}")
    print(f"    -> CJ non trouvé: {not_found}")
