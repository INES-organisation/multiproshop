"""Vérifier les catégories CJ des produits potentiellement mal classés"""
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
        return cj.full_path if cj else f'NOT_FOUND({cid[:12]})'
    except:
        return 'ERROR'

with app.app_context():
    # Vérifier Sports (20 produits - trop peu ?)
    print("=== Sports & Loisirs (20 produits) ===")
    sports = Product.query.filter_by(category_id=100).filter(Product.cj_pid.isnot(None)).all()
    for p in sports:
        print(f"  {p.name[:60]:<60} | {get_cj_path(p)}")
    
    # Vérifier Maison - produits suspects
    print("\n=== Maison - produits enfants/jouets suspects ===")
    maison = Product.query.filter_by(category_id=67).filter(Product.cj_pid.isnot(None)).all()
    suspect_kw = ['rocking horse', 'kids ride', 'ride on', 'ride-on', 'kids bike',
                  'children bike', 'kids car', 'toy ', 'playset', 'playhouse',
                  'canopy tent', 'camping chair', 'camping tent', 'hiking',
                  'bicycle fastening', 'velcro bicycle']
    for p in maison:
        nl = p.name.lower()
        if any(kw in nl for kw in suspect_kw):
            print(f"  {p.name[:60]:<60} | {get_cj_path(p)}")
    
    # Vérifier Animalerie - produits suspects
    print("\n=== Animalerie - produits suspects ===")
    animal = Product.query.filter_by(category_id=178).filter(Product.cj_pid.isnot(None)).all()
    for p in animal:
        nl = p.name.lower()
        if not any(kw in nl for kw in ['pet', 'dog', 'cat', 'bird', 'chicken', 'poultry', 'rabbit', 'fish', 'aquarium', 'hamster', 'parrot']):
            print(f"  {p.name[:60]:<60} | {get_cj_path(p)}")
