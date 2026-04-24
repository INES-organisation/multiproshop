"""Vérifier les catégories CJ des produits dans Sports & Loisirs"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import create_app
from models.product import Product
from models.category import Category
app = create_app()
with app.app_context():
    prods = Product.query.filter_by(category_id=100).filter(Product.cj_pid.isnot(None)).all()
    for p in prods[:10]:
        raw = json.loads(p.cj_raw_data) if p.cj_raw_data else {}
        cid = str(raw.get('categoryId', ''))
        cj = Category.query.filter_by(cj_category_id=cid).first() if cid else None
        path = cj.full_path if cj else 'NOT_FOUND'
        print(f"{p.name[:55]:<55} | CJ: {path}")
