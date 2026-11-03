import os, sys, json, re
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); sys.path.insert(0, ROOT); os.chdir(ROOT)
os.environ.pop('INES_API_KEY', None)
import app as appmod
from extensions import db, cache
from datetime import datetime
app = appmod.create_app('testing'); appmod.app = app
from models.category import Category
from models.product import Product
from models.product_variant import ProductVariant
from models.user import User
from models.role import Role
with app.app_context():
    db.drop_all(); db.create_all(); cache.clear()
    mode = Category(name='Mode', slug='mode', level=1, is_active=True, visible=True); db.session.add(mode); db.session.flush()
    montres = Category(name='Montres', slug='montres', level=2, parent_id=mode.id, is_active=True, visible=True); db.session.add(montres); db.session.flush()
    deep = Category(name='Montres homme', slug='mh', level=3, parent_id=montres.id, is_active=True, visible=True); db.session.add(deep); db.session.flush()
    maison = Category(name='Maison', slug='maison', level=1, is_active=True, visible=True); db.session.add(maison); db.session.flush()
    now = datetime.utcnow()
    w = Product(name='Montre', slug='w', sku='W', price=13.9, cost_price=35.78, stock=5, category_id=deep.id, is_active=True, published_at=now, cj_pid='PW')
    d = Product(name='Brouillon lampe', slug='d', sku='D', price=20, cost_price=5, stock=0, category_id=maison.id, is_active=False, cj_pid='PD')
    loss = Product(name='Perte', slug='l', sku='L', price=5, cost_price=8, stock=9, category_id=maison.id, is_active=False, cj_pid='PL', published_at=now)
    db.session.add_all([w, d, loss]); db.session.flush()
    db.session.add(ProductVariant(product_id=w.id, cj_vid='W1', variant_key='a', price=13.9, stock=3, active=True, cj_raw_data=json.dumps({'price': 6.0})))
    db.session.add(ProductVariant(product_id=w.id, cj_vid='W2', variant_key='b', price=49.9, stock=3, active=True, cj_raw_data=json.dumps({'price': 39.0})))
    ra = Role(name='admin'); db.session.add(ra); db.session.flush()
    a = User(username='boss', email='b@x.com', role_id=ra.id); a.set_password('pw123456'); db.session.add(a)
    db.session.commit(); ids = (w.id, d.id, loss.id); aid = a.id; mode_id = mode.id
    mi = Product.query.get(ids[0]).margin_info(); print(mi)
    assert mi['margin'][0] > 0, mi
cl = app.test_client()
with cl.session_transaction() as s: s['_user_id'] = str(aid); s['_fresh'] = True
def names(qs):
    html = cl.get('/admin/products?' + qs).get_data(as_text=True)
    return [n for n in ('Montre', 'Brouillon lampe', 'Perte') if f'>{n}<' in html or f'{n}</' in html]
assert names(f'category={mode_id}') == ['Montre'], names(f'category={mode_id}')
assert set(names('status=draft')) == {'Brouillon lampe'}
assert names('status=out_of_stock') == [], names('status=out_of_stock')
assert names('status=low_margin') == []
print(names('sort=price_asc'))
html = cl.get('/admin/products').get_data(as_text=True); assert '#dc2626' not in html.split('Montre')[1][:1500]
print('filtres catégorie (sous-catégories), brouillons, rupture, tri, marge par variante OK')
r = cl.post(f'/admin/products/{ids[2]}/toggle'); 
with app.app_context(): assert Product.query.get(ids[2]).is_active is False
r = cl.post('/admin/products/bulk', data={'ids': [ids[1], ids[2]], 'action': 'activate', 'next': '/admin/products'})
with app.app_context():
    assert Product.query.get(ids[1]).is_active and Product.query.get(ids[1]).published_at
    assert Product.query.get(ids[2]).is_active is False
print('activation refusée pour un produit vendu à perte OK')
r = cl.get('/admin/products/export'); print(r.status_code)
with app.app_context():
    c = Category.query.filter_by(slug='maison').first()
    cheap = Product(name='Absurde', slug='abs', sku='AB', price=0.02, cost_price=5, stock=3, category_id=c.id, is_active=False, cj_pid='PAB')
    huge = Product(name='Enorme', slug='en', sku='EN', price=159998.99, cost_price=5, stock=3, category_id=c.id, is_active=False, cj_pid='PEN')
    manual = Product(name='Manuel', slug='ma', sku='MA', price=17.5, cost_price=5, stock=3, category_id=c.id, is_active=False, cj_pid='PMA')
    db.session.add_all([cheap, huge, manual]); db.session.flush()
    vv = ProductVariant(product_id=cheap.id, cj_vid='AB1', variant_key='a', price=10.0, stock=3, active=True, cj_raw_data=json.dumps({'price': 10.0}))
    db.session.add(vv); db.session.commit(); ab, en, ma = cheap.id, huge.id, manual.id
import services.publication as pub
class StockApi:
    def get_variant_inventory(self, vid): return [{'country': 'CN', 'total': 40}]
class Ship:
    def refresh_product_rate(self, product, country): return [{'name': 'CJPacket', 'price': 5.0}]
pub._api = lambda: StockApi(); pub._shipping = lambda: Ship()
r = cl.post('/admin/products/bulk', data={'ids': [ab, en, ma], 'action': 'activate', 'next': '/admin/products'})
with app.app_context():
    a, e, m = Product.query.get(ab), Product.query.get(en), Product.query.get(ma)
    v = ProductVariant.query.filter_by(cj_vid='AB1').first()
    print('prix', a.price, v.price, e.price, m.price)
    assert a.is_active and v.price == 23.9 and a.price == v.price and v.stock == 40 and a.stock == 40, (v.price, v.stock, a.stock)
    assert e.is_active and e.price == 12.9 and m.is_active and m.price == 12.9
print('grille de prix et stock CJ relu à la première publication OK')
