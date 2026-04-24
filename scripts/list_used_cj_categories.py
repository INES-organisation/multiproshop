"""
Liste toutes les catégories CJ L2 et L3 qui ont des produits,
groupées par CJ L1 et leur MPS L1 cible.
Format : CJ L1 > CJ L2 > CJ L3 (nb produits)
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.product import Product
from models.category import Category

app = create_app()

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

with app.app_context():
    # Compter produits par CJ category_id
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
    
    cj_cats = Category.query.filter(Category.cj_category_id.isnot(None)).all()
    cj_by_id = {c.cj_category_id: c for c in cj_cats}
    
    # Construire l'arbre
    # Pour chaque CJ L3 avec des produits, remonter à L2 et L1
    used_l2 = set()
    used_l3 = set()
    
    for cj_id, count in prod_by_cj.items():
        cat = cj_by_id.get(cj_id)
        if not cat:
            continue
        
        if cat.level == 3:
            used_l3.add(cat.id)
            if cat.parent:
                used_l2.add(cat.parent_id)
        elif cat.level == 2:
            used_l2.add(cat.id)
        # L1 est toujours inclus via le mapping
    
    print(f"Catégories CJ L2 utilisées: {len(used_l2)}")
    print(f"Catégories CJ L3 utilisées: {len(used_l3)}")
    
    # Afficher l'arbre complet
    cj_l1s = [c for c in cj_cats if c.level == 1]
    
    total_l2 = 0
    total_l3 = 0
    
    for l1 in sorted(cj_l1s, key=lambda x: x.name):
        mps_id = CJ_L1_TO_MPS.get(l1.name, '?')
        
        l2s = sorted([c for c in cj_cats if c.parent_id == l1.id and c.id in used_l2], key=lambda x: x.name)
        if not l2s:
            continue
        
        print(f"\n{'='*70}")
        print(f"CJ L1: {l1.name} -> MPS ID:{mps_id}")
        print(f"{'='*70}")
        
        for l2 in l2s:
            l2_direct = prod_by_cj.get(l2.cj_category_id, 0)
            l3s = sorted([c for c in cj_cats if c.parent_id == l2.id and c.id in used_l3], key=lambda x: x.name)
            l3_sum = sum(prod_by_cj.get(c.cj_category_id, 0) for c in l3s)
            
            print(f"\n  L2: {l2.name} ({l2_direct + l3_sum} produits)")
            total_l2 += 1
            
            for l3 in l3s:
                l3_count = prod_by_cj.get(l3.cj_category_id, 0)
                print(f"    L3: {l3.name} ({l3_count})")
                total_l3 += 1
    
    print(f"\n{'='*70}")
    print(f"TOTAL: {total_l2} catégories L2, {total_l3} catégories L3 à créer")
