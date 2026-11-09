"""Vitrine Sérénis : catalogue du projet seulement, panier, port, commande et paiement via l'API partenaire."""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); sys.path.insert(0, ROOT); os.chdir(ROOT)
os.environ.pop('INES_API_KEY', None)
TOKEN = 's' * 32
os.environ.update(PARTNER_TOKEN_SERENIS=TOKEN, VITRINE_TOKEN=TOKEN, VITRINE_TESTING='1', MPS_API='http://mps/api/partner')
import app as appmod
from extensions import db, cache
mps = appmod.create_app('testing'); appmod.app = mps
from models.category import Category
from models.product import Product
from models.product_variant import ProductVariant
from models.order import Order
import services.shipping_service as ss
import services.ines_payment as ip


class FakeApi:
    def calculate_shipping(self, products, country, start_country='CN'):
        return [{'logisticName': 'CJPacket', 'logisticPrice': 5.0, 'logisticAging': '12-20'}] if country == 'FR' else []
    def get_variant_inventory(self, vid): return [{'country': 'CN', 'total': 10}]


ss.ShippingService.__init__ = lambda self: setattr(self, 'cj_api', FakeApi())
calls = []
def fake_call(method, path, payload=None):
    calls.append((method, path, payload))
    if method == 'POST':
        return {'id': 'cs_1', 'url': 'https://pay.example/cs_1'}
    return {'id': 'cs_1', 'payment_status': 'paid', 'amount_total': ip.cents(Order.query.first().total_price)}
ip._call = fake_call
ip.enabled = lambda: True
ip.get_session = lambda sid: fake_call('GET', sid)

with mps.app_context():
    db.drop_all(); db.create_all(); cache.clear()
    c = Category(name='Sommeil', slug='s', level=1, is_active=True, visible=True); db.session.add(c); db.session.flush()
    lamp = Product(name='Réveil aube', slug='reveil', sku='S1', price=35.9, cost_price=17.8, stock=50, category_id=c.id,
                   is_active=True, published=True, cj_pid='P1', projects='serenis')
    other = Product(name='Perceuse', slug='perceuse', sku='S2', price=50, cost_price=20, stock=5, category_id=c.id,
                    is_active=True, published=True, cj_pid='P2')
    db.session.add_all([lamp, other]); db.session.flush()
    v = ProductVariant(product_id=lamp.id, cj_vid='V1', variant_key='x', color='Blanc', price=35.9, stock=10, active=True)
    db.session.add(v); db.session.commit()
    pid, other_id, vid = lamp.id, other.id, v.id

# Les appels HTTP de la vitrine arrivent dans MPS (client de test)
import requests
mps_client = mps.test_client()
class Resp:
    def __init__(self, r): self.status_code, self._json = r.status_code, r.get_json()
    def json(self): return self._json
def fake_request(method, url, headers=None, params=None, json=None, timeout=None):
    return Resp(mps_client.open(url.replace('http://mps', ''), method=method, headers=headers, query_string=params, json=json))
requests.request = fake_request

from vitrine.app import app as vitrine
cl = vitrine.test_client()
home = cl.get('/').get_data(as_text=True)
assert 'Réveil aube' in home and 'Perceuse' not in home and 'Sérénis' in home, home[:500]
assert cl.get(f'/produit/{other_id}').status_code == 404  # produit hors projet
page = cl.get(f'/produit/{pid}').get_data(as_text=True)
assert 'Blanc' in page and '35,90' in page
print('catalogue Sérénis OK')

cl.post('/panier/ajouter', data={'product_id': pid, 'variant_id': vid, 'quantity': 2})
assert '71,80' in cl.get('/panier').get_data(as_text=True)
page = cl.get('/commande').get_data(as_text=True)
assert 'CJPacket' in page and '12-20 jours' in page, page
form = dict(first_name='A', last_name='B', email='a@b.fr', phone='0600000000', address='1 rue', city='Paris',
            postal_code='75001', country='FR', shipping_method='CJPacket', step='pay')
r = cl.post('/commande', data=form)
assert r.status_code == 303 and r.headers['Location'] == 'https://pay.example/cs_1', (r.status_code, r.get_data(as_text=True)[:500])
with mps.app_context():
    o = Order.query.first()
    assert o.admin_notes == 'Commande passée sur serenis.multiproshop.com' and o.total_price == round(71.8 + o.shipping_cost, 2), (o.admin_notes, o.total_price)
    params = [c for c in calls if c[0] == 'POST'][-1][2]['params']
    assert params['success_url'].startswith('https://serenis.multiproshop.com/merci?session_id='), params
    o.stripe_session_id = 'cs_1'; db.session.commit()
page = cl.get('/merci?session_id=cs_1').get_data(as_text=True)
assert 'Merci pour votre commande' in page, page
assert cl.get('/panier').get_data(as_text=True).count('Votre panier est vide') == 1
print('commande Sérénis OK')

# Seuil de livraison offerte propre à la vitrine, affiché partout et appliqué par MPS si la marge le permet
os.environ['FREE_SHIPPING_THRESHOLD_SERENIS'] = '39'
import vitrine.app as va
va._shop['data'] = None
home = cl.get('/').get_data(as_text=True)
assert 'Livraison offerte dès 39 €' in home, home[:800]
cl.post('/panier/ajouter', data={'product_id': pid, 'variant_id': vid, 'quantity': 2})
assert 'La livraison est offerte' in cl.get('/panier').get_data(as_text=True)
page = cl.get('/commande').get_data(as_text=True)
assert 'Offerte' in page, page
print('livraison offerte Sérénis OK')

# Avis : ceux déposés sur nos boutiques seulement, jamais ceux importés de CJ
from models.product_review import ProductReview
with mps.app_context():
    db.session.add_all([ProductReview(product_id=pid, author_name='Julie M.', rating=5, comment='Réveil très doux', verified_purchase=True),
                        ProductReview(product_id=pid, author_name='CJ buyer', rating=1, comment='bad', cj_review_id='cj1')])
    db.session.commit()
page = cl.get(f'/produit/{pid}').get_data(as_text=True)
assert 'Réveil très doux' in page and 'CJ buyer' not in page and '1 avis vérifié' in page, page
print('avis Sérénis OK')

# Newsletter : même liste que MPS (source serenis), code -10 % enregistré pour la commande
r = cl.post('/newsletter', data={'email': 'n@b.fr', 'consent': '1'})
assert r.status_code == 302
from models.newsletter import NewsletterSubscriber
from models.coupon import Coupon
with mps.app_context():
    sub = NewsletterSubscriber.query.filter_by(email='n@b.fr').first()
    assert sub and sub.source == 'serenis', sub
    code = sub.coupon_code
page = cl.get('/commande?email=n@b.fr').get_data(as_text=True)
assert code in page and 'Code ' + code in page, page[-3000:]
assert cl.post('/newsletter', data={'email': 'x@b.fr'}).status_code == 302  # sans consentement : refusé
with mps.app_context():
    assert NewsletterSubscriber.query.filter_by(email='x@b.fr').first() is None
form.update(email='n@b.fr')
r = cl.post('/commande', data=form)
assert r.status_code == 303, r.get_data(as_text=True)[-2000:]
with mps.app_context():
    o = Order.query.order_by(Order.id.desc()).first()
    assert o.coupon_code == code and o.discount_amount > 0 and o.total_price == round(o.subtotal - o.discount_amount + o.shipping_cost, 2), (o.coupon_code, o.discount_amount)
print('newsletter et code promo Sérénis OK')

# Lots : seulement avec les produits du projet en ligne
va.RITUALS = [{'name': 'Rituel test', 'text': 'x', 'ids': [pid, other_id]}]
va._shop['data'] = None
assert 'Rituel test' not in cl.get('/').get_data(as_text=True)  # un seul produit Sérénis : pas de lot
with mps.app_context():
    third = Product(name='Plaid', slug='plaid', sku='S3', price=24.9, cost_price=12.3, stock=9, category_id=Category.query.first().id,
                    is_active=True, published=True, cj_pid='P3', projects='serenis')
    db.session.add(third); db.session.commit(); third_id = third.id
va.RITUALS = [{'name': 'Rituel test', 'text': 'x', 'ids': [pid, third_id]}]
va._shop['data'] = None
assert 'Rituel test' in cl.get('/').get_data(as_text=True)
page = cl.get('/rituel/0').get_data(as_text=True)
assert 'Plaid' in page and 'Blanc' in page, page
with cl.session_transaction() as s:
    s['cart'] = []
cl.post('/panier/ajouter-rituel', data={'product_id': [pid, third_id], 'variant_id': [vid, '']})
cart_page = cl.get('/panier').get_data(as_text=True)
assert 'Plaid' in cart_page and 'Réveil aube' in cart_page
print('rituels Sérénis OK')

# E-mails d'une commande Sérénis : au nom de Sérénis, classés « serenis » dans le journal d'INES
import utils.email as ue
sent = []
ue.requests.post = lambda url, json=None, headers=None, timeout=None: (sent.append(json), type('R', (), {'raise_for_status': lambda self: None})())[1]
os.environ['INES_API_KEY'] = 'k'
with mps.app_context():
    o = Order.query.order_by(Order.id.desc()).first()
    assert ue.brand_for(o)['name'] == 'Sérénis'
    ue._send_via_ines('a@b.fr', f'Confirmation de commande {o.order_number} - MultiProShop',
                      "<p>Merci</p><p>L'équipe MultiProShop</p>", 'commande', ue.brand_for(o))
    m = sent[-1]
    assert m['site'] == 'serenis' and m['from_name'] == 'Sérénis' and m['subject'].endswith('- Sérénis'), m
    assert "L'équipe Sérénis" in m['html'] and 'serenis.multiproshop.com' in m['html'], m['html'][:400]
    assert ue.brand_for(Order(admin_notes=None)) is None
# Chiffres pour INES : mois par boutique et inscrits newsletter par source
os.environ['PARTNER_TOKEN_INES'] = 'i' * 32
st = mps.test_client().get('/api/partner/stats', headers={'Authorization': 'Bearer ' + 'i' * 32}).get_json()
assert st['newsletter']['by_source'].get('serenis') == 1 and 'serenis' in st['month_by_site'], st
print('e-mails et chiffres Sérénis OK')
