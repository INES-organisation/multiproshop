import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); sys.path.insert(0, ROOT); os.chdir(ROOT)
os.environ.pop('INES_API_KEY', None)
from app import create_app
from extensions import db
app = create_app('testing')
from models.category import Category
from models.product import Product
from models.product_variant import ProductVariant
with app.app_context():
    db.create_all()
    cat = Category(name='M', slug='m', is_active=True, visible=True, level=1); db.session.add(cat); db.session.flush()
    p = Product(name='Fontaine', slug='f', sku='S', price=23.9, stock=50, category_id=cat.id, is_active=True, cj_pid='P')
    q = Product(name='Laisse', slug='l', sku='S2', price=12.0, stock=50, category_id=cat.id, is_active=True, cj_pid='Q')
    db.session.add_all([p, q]); db.session.flush()
    db.session.add_all([
        ProductVariant(product_id=p.id, cj_vid='V1', color='Black guitar 3pcs', sku='a', price=23.9, stock=5, active=True),
        ProductVariant(product_id=p.id, cj_vid='V2', color='Filter cotton set', sku='b', price=9.9, stock=5, active=True),
        ProductVariant(product_id=p.id, cj_vid='V3', color='Set13', sku='c', price=9.9, stock=5, active=False),
        ProductVariant(product_id=q.id, cj_vid='W1', color='Pink', size='Large', sku='d', price=12.0, stock=5, active=True),
        ProductVariant(product_id=q.id, cj_vid='W2', color='Violet 2Style', size='Small', sku='e', price=12.0, stock=5, active=False),
    ]); db.session.commit()
    ids = p.id, q.id
c = app.test_client()
h = c.get(f'/products/{ids[0]}').get_data(as_text=True)
assert 'Guitare noire 3 pièces' in h and 'Lot de cotons filtrants' in h, 'traduction absente'
assert 'Set13' not in h and 'Lot 13' not in h, 'variante inactive affichée'
h = c.get(f'/products/{ids[1]}').get_data(as_text=True)
assert '>Rose<' in h.replace('\n', '').replace(' ', '') or 'Rose' in h
assert 'Grand' in h, 'taille non traduite'
assert 'Violet 2Style' not in h and 'Modèle 2' not in h and 'Small' not in h and 'Petit' not in h, 'variante inactive affichée'
print('options ok')
