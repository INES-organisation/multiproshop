import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); sys.path.insert(0, ROOT); os.chdir(ROOT)
os.environ.pop('INES_API_KEY', None)
import app as appmod
from extensions import db, cache
app = appmod.create_app('testing'); appmod.app = app
from models.category import Category
from models.product import Product
from models.product_variant import ProductVariant
from models.coupon import Coupon
from models.order import Order
from models.user import User
from models.role import Role
import services.shipping_service as ss
import services.ines_payment as ip
class FakeApi:
    def calculate_shipping(self, products, country, start_country='CN'):
        return [{'logisticName': 'CJPacket', 'logisticPrice': 5.0, 'logisticAging': '14-18'}]
    def get_variant_inventory(self, vid): return [{'country': 'CN', 'total': 10}]
ss.ShippingService.__init__ = lambda self: setattr(self, 'cj_api', FakeApi())
calls = []
def fake_call(method, path, payload=None):
    calls.append(payload)
    if method == 'POST':
        return {'id': 'cs_%d' % len(calls), 'url': 'https://pay.example/cs'}
ip._call = fake_call
ip.enabled = lambda: True
with app.app_context():
    db.drop_all(); db.create_all(); cache.clear()
    c = Category(name='Maison', slug='m', level=1, is_active=True, visible=True); db.session.add(c); db.session.flush()
    p = Product(name='Lampe', slug='lampe', sku='S1', price=30.0, cost_price=10.0, stock=50, category_id=c.id, is_active=True, cj_pid='P1')
    db.session.add(p); db.session.flush()
    v = ProductVariant(product_id=p.id, cj_vid='V1', variant_key='x', price=30.0, stock=10, active=True); db.session.add(v)
    db.session.add_all([Coupon(code='DIX', kind='percent', value=10), Coupon(code='GROS', kind='fixed', value=50),
                        Coupon(code='PORT', kind='shipping'), Coupon(code='MINI', kind='percent', value=5, min_subtotal=100),
                        Coupon(code='OFF', kind='percent', value=5, active=False)])
    ra = Role(name='admin'); db.session.add(ra); db.session.flush()
    a = User(username='boss', email='b@x.com', role_id=ra.id); a.set_password('pw123456'); db.session.add(a)
    db.session.commit(); pid, vid, aid = p.id, v.id, a.id
cl = app.test_client()
cl.post('/cart/add', json={'product_id': pid, 'quantity': 2, 'variant_id': vid})   # 60 €
r = cl.post('/cart/coupon', json={'code': 'nope'}); assert r.status_code == 400 and "n'existe pas" in r.json['message']
r = cl.post('/cart/coupon', json={'code': 'off'}); assert r.status_code == 400
r = cl.post('/cart/coupon', json={'code': 'mini'}); assert r.status_code == 400 and '100.00' in r.json['message'], r.json
r = cl.post('/cart/coupon', json={'code': ' dix '}); assert r.json['success'] and r.json['discount'] == 6.0, r.json
m = cl.post('/cart/shipping-methods', json={'country': 'FR'}).json
assert m['discount'] == 6.0 and m['methods'][0]['price'] == 0, m
page = cl.get('/cart/checkout').get_data(as_text=True); assert 'DIX' in page and '-6.00' in page
form = dict(first_name='A', last_name='B', email='a@b.fr', phone='0600000000', address='1 rue', city='Paris', postal_code='75001', country='FR', shipping_method='CJPacket')
r = cl.post('/cart/checkout', data=form); assert r.status_code == 303, r.status_code
with app.app_context():
    o = Order.query.order_by(Order.id.desc()).first()
    assert (o.discount_amount, o.coupon_code, o.total_price) == (6.0, 'DIX', 54.0), (o.discount_amount, o.coupon_code, o.total_price)
    items = calls[-1]['params']['line_items']
    total = sum(li['price_data']['unit_amount'] * li['quantity'] for li in items)
    assert total == ip.cents(o.total_price), (total, items)
    assert 'x 2' in items[0]['price_data']['product_data']['name']
    ok = ip.fulfill(o.id, {'payment_status': 'paid', 'amount_total': ip.cents(o.total_price), 'id': 'cs'})
    assert ok and Coupon.query.filter_by(code='DIX').first().uses == 1
    assert o.product_margin() is not None and o.product_margin() < 60 - 20
print('code % : remise, total Stripe exact, utilisation comptée OK')
# une fois par client
r = cl.post('/cart/coupon', json={'code': 'DIX', 'email': 'A@B.fr'}); assert r.status_code == 400 and 'déjà été utilisé' in r.json['message'], r.json
# plafonnement : 50 € sur 60 € de panier dont 20 € de coût
r = cl.post('/cart/coupon', json={'code': 'GROS'}); assert r.json['success'], r.json
floor = (20 + 0.25) / (1 - 0.015); assert abs(r.json['discount'] - round(60 - floor, 2)) < 0.02 and 'plafonnée' in r.json['message'], r.json
print('plafond anti-perte OK', r.json['discount'])
# livraison offerte (hors seuil) si la marge la couvre
r = cl.post('/cart/coupon', json={'code': 'PORT'}); assert r.json['success'] and r.json['free_shipping']
m = cl.post('/cart/shipping-methods', json={'country': 'RE'}).json; assert m['methods'][0]['price'] == 0, m
cl.post('/cart/coupon/remove'); m = cl.post('/cart/shipping-methods', json={'country': 'RE'}).json; assert m['methods'][0]['price'] == 4.6
print('livraison offerte par code OK')
# admin
adm = app.test_client()
with adm.session_transaction() as s: s['_user_id'] = str(aid); s['_fresh'] = True
assert adm.get('/admin/coupons').status_code == 200
r = adm.post('/admin/coupons', data={'code': 'noel 15', 'kind': 'percent', 'value': '15', 'once_per_email': '1', 'ends_at': '2026-12-31'})
with app.app_context():
    n = Coupon.query.filter_by(code='NOEL15').first(); assert n and n.value == 15 and n.ends_at.hour == 23
    cid = n.id
assert 'NOEL15' in adm.get('/admin/coupons').get_data(as_text=True)
adm.post(f'/admin/coupons/{cid}/toggle')
with app.app_context(): assert Coupon.query.get(cid).active is False
adm.post(f'/admin/coupons/{cid}/delete')
with app.app_context(): assert Coupon.query.get(cid) is None
print('admin codes promo OK')
