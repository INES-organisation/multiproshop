"""Test rapide de l'API categories/visible pour vérifier compteurs et noms FR"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import app
from models.category import Category
from models.product import Product

with app.app_context():
    # Compter directement les produits par catégorie CJ via cj_raw_data
    products = Product.query.filter(Product.cj_raw_data.isnot(None)).all()
    cj_counts = {}
    for p in products:
        try:
            raw = json.loads(p.cj_raw_data)
            cj_cat_id = raw.get('categoryId') or raw.get('category_id') or ''
            if cj_cat_id:
                cj_cat_id = str(cj_cat_id)
                cj_counts[cj_cat_id] = cj_counts.get(cj_cat_id, 0) + 1
        except:
            pass
    
    # Catégories CJ
    categories = Category.query.filter(Category.cj_category_id.isnot(None)).order_by(Category.level, Category.name).all()
    
    # Index pour cumul
    id_to_cj = {c.id: c.cj_category_id for c in categories}
    cumul = {}
    for c in categories:
        cumul[c.cj_category_id] = cj_counts.get(c.cj_category_id, 0)
    for c in sorted(categories, key=lambda x: -x.level):
        if c.parent_id and c.parent_id in id_to_cj:
            pcj = id_to_cj[c.parent_id]
            if pcj:
                cumul[pcj] = cumul.get(pcj, 0) + cumul.get(c.cj_category_id, 0)
    
    print(f"Total produits avec cj_raw_data: {len(products)}")
    print(f"Total catégories CJ: {len(categories)}")
    print(f"categoryIds distincts trouvés: {len(cj_counts)}")
    
    n1s = [c for c in categories if c.level == 1]
    print(f"\n=== {len(n1s)} CATÉGORIES N1 ===")
    for c in sorted(n1s, key=lambda x: x.name_fr or x.name):
        name = c.name_fr or c.name
        print(f"  {name}: {cumul.get(c.cj_category_id, 0)} produits (champ product_count={c.product_count})")
    
    # Quelques N2
    print(f"\n=== TOP 10 N2 ===")
    n2s = sorted([c for c in categories if c.level == 2], key=lambda x: -cumul.get(x.cj_category_id, 0))
    for c in n2s[:10]:
        name = c.name_fr or c.name
        print(f"  {name}: {cumul.get(c.cj_category_id, 0)} produits")
    
    # Quelques N3
    print(f"\n=== TOP 10 N3 ===")
    n3s = sorted([c for c in categories if c.level == 3], key=lambda x: -cumul.get(x.cj_category_id, 0))
    for c in n3s[:10]:
        name = c.name_fr or c.name
        print(f"  {name}: {cumul.get(c.cj_category_id, 0)} produits")
