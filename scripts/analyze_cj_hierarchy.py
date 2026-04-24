"""
Analyse complète de la hiérarchie des catégories CJ en BDD :
- Combien de niveaux, combien par niveau
- Arbre complet CJ L1 > L2 > L3
- Combien de produits par catégorie CJ L3
- Mapping actuel CJ L1 -> MPS L1
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.product import Product
from models.category import Category
from extensions import db
from sqlalchemy import func

app = create_app()

with app.app_context():
    # 1. Toutes les catégories CJ (ont un cj_category_id)
    cj_cats = Category.query.filter(Category.cj_category_id.isnot(None)).all()
    print(f"Total catégories CJ en BDD: {len(cj_cats)}")
    
    # Par niveau
    by_level = {}
    for c in cj_cats:
        by_level.setdefault(c.level, []).append(c)
    
    for lvl in sorted(by_level.keys()):
        print(f"  Niveau {lvl}: {len(by_level[lvl])} catégories")
    
    # 2. Catégories MPS (sans cj_category_id, niveau 1)
    mps_cats = Category.query.filter(
        Category.cj_category_id.is_(None),
        Category.level == 1
    ).all()
    print(f"\nCatégories MPS niveau 1: {len(mps_cats)}")
    for c in mps_cats:
        count = Product.query.filter_by(category_id=c.id).filter(Product.cj_pid.isnot(None)).count()
        print(f"  ID:{c.id:<4} {c.name:<35} ({count} produits)")
    
    # 3. Arbre CJ complet avec produits
    print(f"\n{'='*90}")
    print("ARBRE CJ COMPLET (L1 > L2 > L3) avec nombre de produits")
    print(f"{'='*90}")
    
    # Compter les produits par categoryId CJ (les 2 formats)
    products = Product.query.filter(Product.cj_pid.isnot(None)).all()
    prod_by_cj = {}
    for p in products:
        if not p.cj_raw_data:
            continue
        try:
            raw = json.loads(p.cj_raw_data)
            cid = str(raw.get('categoryId') or raw.get('category_id') or '')
            if cid:
                prod_by_cj[cid] = prod_by_cj.get(cid, 0) + 1
        except:
            pass
    
    # Catégories CJ L1
    cj_l1 = [c for c in cj_cats if c.level == 1]
    total_mapped = 0
    
    for l1 in sorted(cj_l1, key=lambda x: x.name):
        l1_count = prod_by_cj.get(l1.cj_category_id, 0)
        # Enfants L2
        l2s = [c for c in cj_cats if c.parent_id == l1.id]
        l2_total = sum(prod_by_cj.get(c.cj_category_id, 0) for c in l2s)
        # Enfants L3
        l3_total = 0
        for l2 in l2s:
            l3s = [c for c in cj_cats if c.parent_id == l2.id]
            l3_total += sum(prod_by_cj.get(c.cj_category_id, 0) for c in l3s)
        
        branch_total = l1_count + l2_total + l3_total
        total_mapped += branch_total
        
        print(f"\n  {l1.name} ({branch_total} produits)")
        
        for l2 in sorted(l2s, key=lambda x: x.name):
            l2_count = prod_by_cj.get(l2.cj_category_id, 0)
            l3s = [c for c in cj_cats if c.parent_id == l2.id]
            l3_sum = sum(prod_by_cj.get(c.cj_category_id, 0) for c in l3s)
            sub_total = l2_count + l3_sum
            
            if sub_total > 0:
                print(f"    ├─ {l2.name} ({sub_total})")
                
                for l3 in sorted(l3s, key=lambda x: x.name):
                    l3_count = prod_by_cj.get(l3.cj_category_id, 0)
                    if l3_count > 0:
                        print(f"    │   ├─ {l3.name} ({l3_count})")
    
    print(f"\n  Total produits avec CJ valide: {total_mapped}")
    print(f"  Total produits CJ: {len(products)}")
    print(f"  Orphelins (sans CJ valide): {len(products) - total_mapped}")
    
    # 4. Résumé des catégories CJ L1 et leur mapping MPS actuel
    print(f"\n{'='*90}")
    print("MAPPING CJ L1 -> MPS L1 ACTUEL")
    print(f"{'='*90}")
    
    CJ_L1_TO_MPS = {
        'Phones & Accessories': 38,
        'Computer & Office': 22,
        'Home, Garden & Furniture': 67,
        "Women's Clothing": 52,
        'Jewelry & Watches': 52,
        "Men's Clothing": 52,
        'Bags & Shoes': 52,
        'Health, Beauty & Hair': 87,
        'Automobiles & Motorcycles': 139,
        'Sports & Outdoors': 100,
        'Home Improvement': 152,
        'Pet Supplies': 178,
        'Consumer Electronics': 1,
        'Toys, Kids & Babies': 126,
    }
    
    for l1 in sorted(cj_l1, key=lambda x: x.name):
        mps_id = CJ_L1_TO_MPS.get(l1.name, '?')
        mps = db.session.get(Category, mps_id) if isinstance(mps_id, int) else None
        print(f"  {l1.name:<35} -> {mps.name if mps else '?'} (ID:{mps_id})")
