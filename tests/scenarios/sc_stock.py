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
    p = Product(name='Dress', slug='d', sku='S', price=20.0, stock=50, category_id=cat.id, is_active=True, cj_pid='P')
    q = Product(name='Empty', slug='e', sku='S2', price=20.0, stock=0, category_id=cat.id, is_active=True, cj_pid='Q')
    db.session.add_all([p, q]); db.session.flush()
    v = ProductVariant(product_id=p.id, cj_vid='V', variant_key='R', sku='V1', price=20.0, stock=0, active=True)
    w = ProductVariant(product_id=q.id, cj_vid='W', variant_key='R', sku='W1', price=20.0, stock=0, active=True)
    db.session.add_all([v, w]); db.session.commit()
    ids = p.id, v.id, q.id, w.id
c = app.test_client()
r = c.post('/cart/add', json={'product_id': ids[0], 'quantity': 1, 'variant_id': ids[1]}); print(r.status_code, r.json.get('message'))
assert r.status_code == 200
r = c.post('/cart/add', json={'product_id': ids[2], 'quantity': 1, 'variant_id': ids[3]}); print(r.status_code, r.json.get('message'))
assert r.status_code == 400
print('stock ok')
r = c.post('/cart/add', json={'product_id': ids[0], 'quantity': 1, 'variant_id': ids[1]})
r = c.get('/cart/checkout'); print('checkout', r.status_code, r.headers.get('Location'))
assert r.status_code == 200, 'checkout bloqué'
with app.app_context():
    from models.product import Product
    pr = db.session.get(Product, ids[0]); pr.is_active = False; db.session.commit()
from extensions import cache
with app.app_context(): cache.clear()
r = c.get(f'/products/{ids[0]}'); assert r.status_code == 302, r.status_code
r = c.post('/cart/add', json={'product_id': ids[0], 'quantity': 1, 'variant_id': ids[1]}); assert r.status_code == 404
print('inactif ok')
