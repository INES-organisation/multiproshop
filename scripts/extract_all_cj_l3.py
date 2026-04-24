"""
Extraire TOUTES les catégories CJ niveau 3 avec leur chemin complet (L1 > L2 > L3)
et le nombre de produits réels dans chaque catégorie L3.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.product import Product
from models.category import Category
from extensions import db

app = create_app()

with app.app_context():
    # Compter les produits par cj_category_id (depuis raw_data)
    products = Product.query.filter(Product.cj_pid.isnot(None)).all()
    
    prod_count_by_cj = {}
    for p in products:
        if not p.cj_raw_data:
            continue
        try:
            raw = json.loads(p.cj_raw_data)
        except:
            continue
        cj_id = str(raw.get('categoryId') or '')
        if cj_id:
            prod_count_by_cj[cj_id] = prod_count_by_cj.get(cj_id, 0) + 1
    
    # Extraire toutes les catégories CJ L3 (les produits sont au niveau 3)
    cj_l3_cats = Category.query.filter(
        Category.cj_category_id.isnot(None),
        Category.level == 3
    ).all()
    
    # Construire la structure L1 > L2 > L3
    structure = {}
    for cat3 in cj_l3_cats:
        cat2 = cat3.parent
        if not cat2:
            continue
        cat1 = cat2.parent
        if not cat1:
            continue
        
        l1 = cat1.name
        l2 = cat2.name
        l3 = cat3.name
        count = prod_count_by_cj.get(cat3.cj_category_id, 0)
        
        if l1 not in structure:
            structure[l1] = {}
        if l2 not in structure[l1]:
            structure[l1][l2] = []
        structure[l1][l2].append({
            'name': l3,
            'cj_id': cat3.cj_category_id,
            'count': count,
            'db_id': cat3.id,
        })
    
    # Afficher avec le nombre de produits
    total_with_products = 0
    total_l3 = 0
    
    for l1 in sorted(structure.keys()):
        l1_total = sum(item['count'] for l2_items in structure[l1].values() for item in l2_items)
        print(f"\n{'='*90}")
        print(f"L1: {l1} ({l1_total} produits)")
        print(f"{'='*90}")
        
        for l2 in sorted(structure[l1].keys()):
            l2_total = sum(item['count'] for item in structure[l1][l2])
            print(f"\n  L2: {l2} ({l2_total} produits)")
            
            for item in sorted(structure[l1][l2], key=lambda x: x['count'], reverse=True):
                total_l3 += 1
                if item['count'] > 0:
                    total_with_products += 1
                    marker = "***" if item['count'] > 0 else "   "
                    print(f"    {marker} L3: {item['name']:<45} | {item['count']:>5} produits | CJ:{item['cj_id'][:20]}...")
    
    print(f"\n\nTotal catégories L3: {total_l3}")
    print(f"L3 avec produits: {total_with_products}")
    print(f"Total produits mappés: {sum(prod_count_by_cj.values())}")
