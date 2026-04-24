"""
Analyser les produits dans Sports & Loisirs (100) pour identifier ceux mal placés.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.product import Product
from models.category import Category
from extensions import db

app = create_app()

with app.app_context():
    prods = Product.query.filter_by(category_id=100).filter(
        Product.cj_pid.isnot(None)
    ).all()
    
    print(f"Sports & Loisirs: {len(prods)} produits\n")
    
    for p in prods:
        raw = json.loads(p.cj_raw_data) if p.cj_raw_data else {}
        cj_cat_id = str(raw.get('categoryId', ''))
        cj_cat_name = raw.get('categoryName', '')
        
        cj_cat = Category.query.filter_by(cj_category_id=cj_cat_id).first() if cj_cat_id else None
        cj_path = cj_cat.full_path if cj_cat else f"NOT_FOUND({cj_cat_id})"
        
        print(f"  ID:{p.id:5} | {p.name[:55]:<55} | CJ: {cj_path[:50]}")
        if cj_cat_name and not cj_cat:
            print(f"         categoryName: {cj_cat_name}")
