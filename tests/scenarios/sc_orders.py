import os, sys, re, json
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); sys.path.insert(0, ROOT); os.chdir(ROOT)
os.environ.pop('INES_API_KEY', None)
import app as appmod
from extensions import db, cache
app = appmod.create_app('testing')
from models.category import Category
from models.product import Product
from models.user import User
from models.role import Role
from models.order import Order
with app.app_context():
    db.drop_all(); db.create_all(); cache.clear()
    c = Category(name='Animalerie', slug='a', level=1, is_active=True, visible=True); db.session.add(c); db.session.flush()
    p = Product(name='Arbre', slug='arbre', sku='S1', price=39.9, cost_price=12.0, stock=50, category_id=c.id, is_active=True, cj_pid='P1'); db.session.add(p)
    r = Role(name='admin'); db.session.add(r); db.session.flush()
    u = User(username='boss', email='b@x.com', role_id=r.id); u.set_password('pw123456'); db.session.add(u)
    db.session.commit()
cl = app.test_client()
cl.post('/auth/admin-login', data={'username': 'boss', 'password': 'pw123456'})
from models.order import Order, OrderItem
from datetime import datetime
with app.app_context():
    for i,(ps,note) in enumerate([('paid',None),('paid','Commande interne admin, au prix coûtant CJ'),('pending',None)]):
        o=Order(order_number=f'MPS{i}',status='paid' if ps=='paid' else 'pending',payment_status=ps,total_price=50+i,subtotal=50,customer_email='a@b.c',shipping_first_name='A',shipping_last_name='B',shipping_address='x',shipping_city='y',shipping_postal_code='97400',shipping_country='RE',admin_notes=note)
        db.session.add(o); db.session.flush()
        db.session.add(OrderItem(order_id=o.id,product_id=1,quantity=2,price=25))
    db.session.commit()
r = cl.get('/admin/orders'); h = r.get_data(as_text=True)
assert r.status_code == 200 and '#MPS0' in h and 'à envoyer' in h and 'interne' in h, (r.status_code, h[-2000:])
with app.app_context():
    oid = Order.query.first().id
r = cl.get(f'/admin/orders/{oid}'); print('detail', r.status_code)
# marge : 2 x 25 - 2 x 12 (coût produit) - frais
assert '24.' in h or '25.' in h
# actions groupées
with app.app_context():
    c2 = Category(name='Outillage', slug='outillage', level=1, is_active=True, visible=True); db.session.add(c2)
    p = Product.query.first(); p.is_active = False; p.published_at = None
    p.short_description = 'Léger et solide\nBatterie 2 h\n- Livré avec coffret'
    db.session.commit(); pid, c2id = p.id, c2.id
r = cl.post('/admin/products/bulk', data={'ids': [str(pid)], 'action': 'activate', 'next': '/admin/products?status=inactive'})
assert r.status_code == 302 and r.headers['Location'].endswith('/admin/products?status=inactive')
r = cl.post('/admin/products/bulk', data={'ids': [str(pid)], 'action': 'category', 'category_id': str(c2id), 'next': 'https://evil.com'})
assert r.headers['Location'].endswith('/admin/products')
with app.app_context():
    p = Product.query.get(pid); assert p.is_active and p.published_at and p.category_id == c2id
assert 'bulk-form' in cl.get('/admin/products').get_data(as_text=True)
p.cj_pid = 'P1'
h = cl.get(f'/products/{pid}').get_data(as_text=True)
assert 'product-bullets' in h and 'Livré avec coffret' in h and 'ID Produit CJ' not in h
print('TOUT OK commandes, actions groupées, puces')
