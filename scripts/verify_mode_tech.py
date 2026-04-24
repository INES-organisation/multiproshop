"""Vérifier les produits 'tech' dans Mode - sont-ils vraiment mal placés ?"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import create_app
from models.product import Product
from models.category import Category
from extensions import db

app = create_app()

with app.app_context():
    mode_prods = Product.query.filter_by(category_id=52).filter(Product.cj_pid.isnot(None)).all()
    
    # Vérifier chaque produit "tech" dans Mode avec sa catégorie CJ originale
    tech_kw = ['monitor', 'laptop', 'computer', 'phone case', 'bluetooth', 'camera', 'drone', 'sensor']
    
    real_problems = []
    false_positives = []
    
    for p in mode_prods:
        nl = p.name.lower()
        if not any(kw in nl for kw in tech_kw):
            continue
        
        # Vérifier la catégorie CJ originale
        cj_l1 = '?'
        if p.cj_raw_data:
            try:
                raw = json.loads(p.cj_raw_data)
                cid = str(raw.get('categoryId', ''))
                if cid:
                    cj = Category.query.filter_by(cj_category_id=cid).first()
                    if cj:
                        c = cj
                        while c.parent and c.level > 1:
                            c = c.parent
                        cj_l1 = c.name
            except:
                pass
        
        # Si la catégorie CJ L1 est vêtements/sacs/bijoux -> c'est correct dans Mode
        mode_cj = ["Women's Clothing", "Men's Clothing", "Bags & Shoes", "Jewelry & Watches",
                    "Toys, Kids & Babies", "Sports & Outdoors"]
        
        if cj_l1 in mode_cj:
            false_positives.append(f"  OK  {p.name[:55]:<55} | CJ: {cj_l1}")
        else:
            real_problems.append(f"  BAD {p.name[:55]:<55} | CJ: {cj_l1} -> devrait être ailleurs")
    
    print(f"Produits 'tech' dans Mode: {len(real_problems) + len(false_positives)}")
    print(f"  Faux positifs (correct dans Mode): {len(false_positives)}")
    print(f"  Vrais problèmes: {len(real_problems)}")
    
    if real_problems:
        print("\n--- Vrais problèmes ---")
        for r in real_problems[:20]:
            print(r)
    
    if false_positives:
        print(f"\n--- Exemples de faux positifs (10 premiers) ---")
        for f in false_positives[:10]:
            print(f)
