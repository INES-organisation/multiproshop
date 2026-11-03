import os, sys, json
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); sys.path.insert(0, ROOT); os.chdir(ROOT)
os.environ.pop('INES_API_KEY', None)
import app as appmod
from extensions import db, cache
from datetime import datetime
app = appmod.create_app('testing'); appmod.app = app
from models.category import Category
from models.product import Product
from models.user import User
from models.role import Role
with app.app_context():
    db.drop_all(); db.create_all(); cache.clear()
    tech = Category(name='Tech', slug='t', level=1, is_active=True, visible=True, cj_category_id='C1'); db.session.add(tech); db.session.flush()
    drones = Category(name='Drones', slug='d', level=2, parent_id=tech.id, is_active=True, visible=True); db.session.add(drones); db.session.flush()
    other = Category(name='Maison', slug='m', level=1, is_active=True, visible=True); db.session.add(other); db.session.flush()
    on = Product(name='Drone A', slug='a', sku='A', price=60, cost_price=20, stock=5, category_id=drones.id, is_active=True, published_at=datetime.utcnow(), cj_pid='PA')
    new = Product(name='Drone B', slug='b', sku='B', price=80, cost_price=30, stock=5, category_id=drones.id, is_active=False, cj_pid='PB')
    raw = Product(name='Caméra C', slug='c', sku='C', price=40, cost_price=10, stock=0, category_id=other.id, is_active=False, cj_pid='PC', cj_raw_data=json.dumps({'categoryId': 'C1'}))
    loss = Product(name='Perte D', slug='dd', sku='D', price=5, cost_price=9, stock=3, category_id=other.id, is_active=False, cj_pid='PD', published_at=datetime.utcnow())
    db.session.add_all([on, new, raw, loss])
    ra = Role(name='admin'); db.session.add(ra); db.session.flush()
    a = User(username='boss', email='b@x.com', role_id=ra.id); a.set_password('pw123456'); db.session.add(a)
    db.session.commit(); aid, tid = a.id, tech.id; ids = {p.name: p.id for p in (on, new, raw, loss)}
cl = app.test_client()
with cl.session_transaction() as s: s['_user_id'] = str(aid); s['_fresh'] = True
assert cl.get('/admin/cj/products').status_code == 200
def names(**data):
    r = cl.post('/admin/api/cj/products/by-category', data=data); assert r.status_code == 200, r.get_data(as_text=True)[:300]
    return sorted(p['name'] for p in r.json['products'])
assert names(category_id='all') == ['Caméra C', 'Drone A', 'Drone B', 'Perte D']
assert names(category_id=str(tid)) == ['Caméra C', 'Drone A', 'Drone B'], names(category_id=str(tid))
assert names(category_id='all', status='never') == ['Caméra C', 'Drone B']
assert names(category_id='all', status='published') == ['Drone A']
r = cl.post('/admin/api/cj/products/by-category', data={'category_id': 'all', 'sort': 'price_desc'}); assert [p['price'] for p in r.json['products']] == [80, 60, 40, 5]
r = cl.post('/admin/api/cj/products/search', data={'search': 'drone', 'status': 'never'}); assert [p['name'] for p in r.json['products']] == ['Drone B'], r.json
card = [p for p in cl.post('/admin/api/cj/products/by-category', data={'category_id': 'all'}).json['products'] if p['name'] == 'Drone A'][0]
assert card['margin'] == 40 and card['category'] == 'Drones'
print('liste CJ : tous, catégorie + sous-catégories + catégorie CJ, statut, tri, recherche OK')
r = cl.post(f"/admin/api/cj/product/{ids['Drone B']}/publish", json={'active': True}); assert r.json['success'] and r.json['is_active']
r = cl.post(f"/admin/api/cj/product/{ids['Perte D']}/publish", json={'active': False}); assert r.json['success']
r = cl.post(f"/admin/api/cj/product/{ids['Perte D']}/publish", json={'active': True}); assert r.status_code == 400 and 'perte' in r.json['message']
with app.app_context(): assert Product.query.get(ids['Drone B']).published_at is not None
print('publier / retirer depuis la page CJ, refus à perte OK')
