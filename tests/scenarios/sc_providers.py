"""Multi-fournisseur : port additionné par fournisseur, commande CJ limitée à sa part, autre fournisseur signalé."""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); sys.path.insert(0, ROOT); os.chdir(ROOT)
os.environ.pop('INES_API_KEY', None)
import app as appmod
from extensions import db, cache
app = appmod.create_app('testing')
from models.category import Category
from models.product import Product
from models.product_variant import ProductVariant
from models.order import Order, OrderItem
import services.shipping_service as ss
from services import providers


class FakeApi:
    def calculate_shipping(self, products, country, start_country='CN'):
        return [{'logisticName': 'CJPacket', 'logisticPrice': 5.0, 'logisticAging': '10-15'}] if country == 'FR' else []
    def get_variant_inventory(self, vid): return []
    def _make_request(self, *a, **k): return None


ss.ShippingService.__init__ = lambda self: setattr(self, 'cj_api', FakeApi())
with app.app_context():
    db.drop_all(); db.create_all(); cache.clear()
    c = Category(name='Maison', slug='m', level=1, is_active=True, visible=True); db.session.add(c); db.session.flush()
    cj = Product(name='Lampe', slug='lampe', sku='S1', price=30.0, cost_price=25.0, stock=50, category_id=c.id, is_active=True, cj_pid='P1')
    eu = Product(name='Chaise', slug='chaise', sku='S2', price=80.0, cost_price=70.0, stock=50, category_id=c.id, is_active=True,
                 cj_pid='P2', provider='bigbuy')
    db.session.add_all([cj, eu]); db.session.flush()
    v1 = ProductVariant(product_id=cj.id, cj_vid='V1', variant_key='x', price=30.0, stock=10, active=True)
    db.session.add(v1); db.session.commit()
    ids, vid = (cj.id, eu.id), v1.id

cl = app.test_client()
cl.post('/cart/add', json={'product_id': ids[0], 'quantity': 1, 'variant_id': vid})
cl.post('/cart/add', json={'product_id': ids[1], 'quantity': 1})

# Fournisseur pas encore branché : aucun port, le panier ne peut pas être payé
r = cl.post('/cart/shipping-methods', json={'country': 'FR'}).json
assert r['methods'] == [], r

# Branché : une méthode qui additionne les deux ports
providers.QUOTERS['bigbuy'] = lambda items, country: {'methods': [
    {'code': 'GLS', 'name': 'GLS', 'price': 9.9, 'delivery_time': '3-5'},
    {'code': 'DHL', 'name': 'DHL', 'price': 19.0, 'delivery_time': '1-2'}]}
m = cl.post('/cart/shipping-methods', json={'country': 'FR'}).json['methods']
assert len(m) == 1 and m[0]['code'] == 'cj:CJPacket|bigbuy:GLS' and m[0]['price'] == round(4.6 + 9.9, 2), m
print('port par fournisseur OK')

# Panier CJ seul : méthodes inchangées
with cl.session_transaction() as s: s['cart'] = {}
cl.post('/cart/add', json={'product_id': ids[0], 'quantity': 1, 'variant_id': vid})
m = cl.post('/cart/shipping-methods', json={'country': 'FR'}).json['methods']
assert [x['code'] for x in m] == ['CJPacket'], m

# Commande payée : CJ ne reçoit que sa part, avec sa méthode ; BigBuy (non branché) est signalé
from services.cj_order_service import CjOrderService
import services.notifications as notifications
sent = []
notifications.notify = lambda *a, **k: sent.append(a)
with app.app_context():
    o = Order(order_number='T1', customer_email='a@b.c', shipping_first_name='A', shipping_last_name='B', shipping_address='x',
              shipping_city='y', shipping_postal_code='75001', shipping_country='FR', shipping_method='cj:CJPacket|bigbuy:GLS')
    db.session.add(o); db.session.flush()
    db.session.add_all([OrderItem(order_id=o.id, product_id=ids[0], variant_id=vid, quantity=1, price=30),
                        OrderItem(order_id=o.id, product_id=ids[1], quantity=1, price=80)])
    db.session.commit()
    data = CjOrderService.__new__(CjOrderService)._prepare_order_data(o)
    assert [p['pid'] for p in data['products']] == ['P1'] and data['logisticsName'] == 'CJPacket', data
    providers.PLACERS['cj'] = lambda order: {'success': True}
    providers.dispatch(o)
    assert len(sent) == 1 and 'BigBuy' in sent[0][1], sent
print('commande par fournisseur OK')
