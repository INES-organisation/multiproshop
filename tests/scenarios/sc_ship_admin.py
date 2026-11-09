import os, sys, json, re
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); sys.path.insert(0, ROOT); os.chdir(ROOT)
os.environ.pop('INES_API_KEY', None)
import app as appmod
from extensions import db, cache
app = appmod.create_app('testing')
from models.category import Category
from models.product import Product
from models.product_variant import ProductVariant
from models.user import User
from models.role import Role
import services.shipping_service as ss
calls = []
class FakeApi:
    def calculate_shipping(self, products, country):
        calls.append((country, products))
        if country == 'RE': return [{'logisticName': 'CJPacket', 'logisticPrice': 10.0, 'logisticAging': '10-20'}]
        if country == 'XX': return []
        return None
    def _make_request(self, *a, **k): return None
with app.app_context():
    db.drop_all(); db.create_all(); cache.clear()
    c = Category(name='Animalerie', slug='a', level=1, is_active=True, visible=True); db.session.add(c); db.session.flush()
    p = Product(name='Arbre à chat', slug='arbre', sku='S1', price=39.9, cost_price=12.0, stock=50, category_id=c.id, is_active=True, cj_pid='P1')
    db.session.add(p); db.session.flush()
    v = ProductVariant(product_id=p.id, cj_vid='V1', variant_key='Grey', price=39.9, stock=0, active=True, cj_raw_data=json.dumps({'price': 10.0}))
    db.session.add(v)
    role = Role(name='admin'); db.session.add(role); db.session.flush()
    u = User(username='boss', email='Boss@Example.com', role_id=role.id); u.set_password('ancienmdp1'); db.session.add(u)
    db.session.commit(); pid, vidid = p.id, v.id
orig_init = ss.ShippingService.__init__
def init(self): self.cj_api = FakeApi()
ss.ShippingService.__init__ = init
cl = app.test_client()
cl.post('/cart/add', json={'product_id': pid, 'quantity': 2, 'variant_id': vidid})
r = cl.post('/cart/shipping-methods', json={'country': 'RE'}).json
assert r['source'] == 'cj' and r['methods'][0]['price'] == 9.2, r
assert calls[-1] == ('RE', [{'vid': 'V1', 'quantity': 2}]), calls
r = cl.post('/cart/shipping-methods', json={'country': 'RE'}).json; assert len(calls) == 1, 'cache'
r = cl.post('/cart/shipping-methods', json={'country': 'XX'}).json
assert r['methods'] == [] and 'indisponible' in r['message'], r
r = cl.post('/cart/shipping-methods', json={'country': 'BE'}).json
assert r['methods'] == [], r  # CJ muet et pas de cache : plus de tarifs inventés
h = cl.get('/cart/checkout').get_data(as_text=True)
assert 'La Réunion' in h and 'Mode admin' not in h
print('livraison ok')
# admin : prix coûtant
ca = app.test_client()
r = ca.post('/auth/connexion', data={'email': 'Boss@Example.com', 'username': 'boss', 'password': 'ancienmdp1'}, follow_redirects=True)
ca.post('/cart/add', json={'product_id': pid, 'quantity': 1, 'variant_id': vidid})
h = ca.get('/cart/').get_data(as_text=True)
import re as _r; print('admin connecté', 'Mode admin' in h, _r.findall(r'(\d+[.,]\d\d) ?€', h)[:6], ca.get('/').status_code)
with app.test_request_context():
    from flask_login import login_user
    from models.cart import Cart, cost_price
    with app.app_context():
        u = User.query.filter_by(username='boss').first(); v = ProductVariant.query.get(vidid); p = Product.query.get(pid)
        assert cost_price(p, v) == 9.2 and cost_price(p) == 12.0
print('coût ok')
# mot de passe oublié
import utils.email as ue
sent = []
ue._send_via_ines = lambda to, subject, html, template=None, brand=None: sent.append((to, html))
import threading
r = cl.post('/auth/forgot-password', data={'email': 'boss@example.com'})
import time; time.sleep(0.5)
assert sent and sent[0][0] == 'Boss@Example.com', sent
link = re.search(r'href="([^"]+/auth/reinitialiser/[^"]+)"', sent[0][1]).group(1)
path = link.split('localhost')[-1]
assert cl.get(path).status_code == 200
r = cl.post(path, data={'password': 'nouveau123', 'password_confirm': 'nouveau123'})
assert r.status_code == 302
with app.app_context():
    assert User.query.filter_by(username='boss').first().check_password('nouveau123')
assert cl.get(path).status_code == 302, 'lien à usage unique'
r = cl.post('/auth/forgot-password', data={'email': 'inconnu@x.com'}); assert r.status_code == 302 and len(sent) == 1
print('TOUT OK livraison admin mdp')
