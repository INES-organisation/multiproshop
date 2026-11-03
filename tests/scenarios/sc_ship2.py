import os, sys, json
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); sys.path.insert(0, ROOT); os.chdir(ROOT)
os.environ.pop('INES_API_KEY', None)
import app as appmod
from extensions import db, cache
app = appmod.create_app('testing')
from models.category import Category
from models.product import Product
from models.product_variant import ProductVariant
import services.shipping_service as ss
calls = []
class FakeApi:
    def calculate_shipping(self, products, country, start_country='CN'):
        calls.append((start_country, country, [p['vid'] for p in products]))
        vids = {p['vid'] for p in products}
        if 'VFR' in vids:  # entrepôt France seulement
            return [{'logisticName': 'Colissimo', 'logisticPrice': 0, 'logisticAging': '3-7'}] if start_country == 'FR' else []
        if country == 'FR':
            q = sum(p['quantity'] for p in products)
            return [{'logisticName': 'CJPacket', 'logisticPrice': 5.0 * q, 'logisticAging': '14-18'},
                    {'logisticName': 'DHL', 'logisticPrice': 40.0, 'logisticAging': '5-8'}]
        return []
    def get_variant_inventory(self, vid):
        calls.append(('stock', vid))
        return [{'country': 'FR', 'total': 30}, {'country': 'CN', 'total': 0}]
    def _make_request(self, *a, **k): return None
with app.app_context():
    db.drop_all(); db.create_all(); cache.clear()
    c = Category(name='Maison', slug='m', level=1, is_active=True, visible=True); db.session.add(c); db.session.flush()
    cheap = Product(name='Lampe', slug='lampe', sku='S1', price=60.0, cost_price=20.0, stock=50, category_id=c.id, is_active=True, cj_pid='P1')
    thin = Product(name='Piano', slug='piano', sku='S2', price=55.0, cost_price=50.0, stock=50, category_id=c.id, is_active=True, cj_pid='P2')
    fr = Product(name='Tapis', slug='tapis', sku='S3', price=30.0, cost_price=10.0, stock=50, category_id=c.id, is_active=True, cj_pid='P3')
    db.session.add_all([cheap, thin, fr]); db.session.flush()
    for p, vid in ((cheap, 'V1'), (thin, 'V2'), (fr, 'VFR')):
        db.session.add(ProductVariant(product_id=p.id, cj_vid=vid, variant_key='x', price=p.price, stock=10, active=True))
    db.session.commit(); ids = (cheap.id, thin.id, fr.id)
    vids = [ProductVariant.query.filter_by(product_id=i).first().id for i in ids]
ss.ShippingService.__init__ = lambda self: setattr(self, 'cj_api', FakeApi())
cl = app.test_client()

# Marge positive : port offert
cl.post('/cart/add', json={'product_id': ids[0], 'quantity': 1, 'variant_id': vids[0]})
m = cl.post('/cart/shipping-methods', json={'country': 'FR'}).json['methods']
assert m[0]['price'] == 0 and m[0]['code'] == 'CJPacket', m
# Panier à marge trop faible : port payant
cl.post('/cart/clear'); cl.get('/cart/clear')
with cl.session_transaction() as s: s['cart'] = {}
cl.post('/cart/add', json={'product_id': ids[1], 'quantity': 1, 'variant_id': vids[1]})
m = cl.post('/cart/shipping-methods', json={'country': 'FR'}).json['methods']
assert m[0]['price'] == 4.6, m
print('livraison offerte selon la marge OK')

# Entrepôt France : route depuis FR
with cl.session_transaction() as s: s['cart'] = {}
cl.post('/cart/add', json={'product_id': ids[2], 'quantity': 1, 'variant_id': vids[2]})
r = cl.post('/cart/shipping-methods', json={'country': 'FR'}).json
assert r['success'] and r['methods'][0]['code'] == 'Colissimo' and r['methods'][0]['from'] == 'FR', r
assert ('FR', 'FR', ['VFR']) in calls and ('stock', 'VFR') in calls, calls
print('entrepôt France OK')
# Une route Chine qui marche n'interroge pas le stock
n = len([c for c in calls if c[0] == 'stock'])
cl.get(f'/products/{ids[0]}/livraison?country=FR')
assert len([c for c in calls if c[0] == 'stock']) == n

# Estimation fiche produit
r = cl.get(f'/products/{ids[0]}/livraison?country=FR').json
assert r['available'] and r['cheapest']['price'] == 4.6 and r['cheapest']['days'] == [14, 18] and r['fastest']['name'] == 'DHL' and len(r['cheapest']['dates']) == 2, r
r = cl.get(f'/products/{ids[0]}/livraison?country=RE').json
assert r['success'] and r['available'] is False, r
assert cl.get(f'/products/{ids[0]}/livraison?country=US').status_code == 400
h = cl.get(f'/products/{ids[0]}').get_data(as_text=True)
assert 'shipping-country' in h and 'La Réunion' in h
print('estimation fiche produit OK')

# Commande CJ : entrepôt de départ
from models.order import Order, OrderItem
from services.cj_order_service import CjOrderService
with app.app_context():
    o = Order(order_number='T1', customer_email='a@b.c', shipping_first_name='A', shipping_last_name='B', shipping_address='x',
              shipping_city='y', shipping_postal_code='75001', shipping_country='FR', shipping_method='Colissimo')
    db.session.add(o); db.session.flush()
    v = ProductVariant.query.filter_by(cj_vid='VFR').first()
    db.session.add(OrderItem(order_id=o.id, product_id=ids[2], variant_id=v.id, quantity=1, price=30)); db.session.commit()
    svc = CjOrderService.__new__(CjOrderService)
    assert CjOrderService._from_country(o) == 'FR'
    data = svc._prepare_order_data(o)
    assert data['fromCountryCode'] == 'FR' and data['logisticsName'] == 'Colissimo', data
print('commande CJ depuis la France OK')
