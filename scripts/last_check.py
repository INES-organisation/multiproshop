"""Dernière vérification : produits suspects dans Électronique et Bricolage"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import create_app
from models.product import Product
from models.category import Category
app = create_app()

def get_cj_path(p):
    if not p.cj_raw_data:
        return '?'
    try:
        raw = json.loads(p.cj_raw_data)
        cid = str(raw.get('categoryId') or raw.get('category_id') or '')
        if not cid:
            return 'NO_CID'
        cj = Category.query.filter_by(cj_category_id=cid).first()
        return cj.full_path if cj else 'NOT_FOUND'
    except:
        return 'ERROR'

with app.app_context():
    print("=== Électronique & High-Tech (26 produits) - TOUS ===")
    elec = Product.query.filter_by(category_id=1).filter(Product.cj_pid.isnot(None)).all()
    for p in elec:
        print(f"  {p.name[:55]:<55} | {get_cj_path(p)}")
    
    print(f"\n=== Bricolage & Outillage (21 produits) - TOUS ===")
    brico = Product.query.filter_by(category_id=152).filter(Product.cj_pid.isnot(None)).all()
    for p in brico:
        print(f"  {p.name[:55]:<55} | {get_cj_path(p)}")
