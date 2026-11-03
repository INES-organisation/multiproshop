import os, sys, json, re
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); sys.path.insert(0, ROOT)
os.chdir(ROOT)
os.environ.pop('INES_API_KEY', None)
from app import create_app
from extensions import db
app = create_app('testing')
from models.category import Category
from models.product import Product
from models.product_variant import ProductVariant
from models.order import Order, OrderItem

with app.app_context():
    db.create_all()
    cat = Category(name='Maison', slug='maison', is_active=True, visible=True, level=1)
    db.session.add(cat); db.session.flush()
    p = Product(name='Motorcycle Phone Holder', slug='holder', sku='SKU1', price=30.0, stock=50, category_id=cat.id, is_active=True, cj_pid='PID1', image_url='https://cf.cjdropshipping.com/a.jpg', description='<p>Support "solide" pour vélo</p>')
    p2 = Product(name='LED Desk Lamp', slug='lamp', sku='SKU2', price=12.0, stock=50, category_id=cat.id, is_active=True, cj_pid='PID2', sales_count=5)
    p3 = Product(name='Dress with variants', slug='dress', sku='SKU3', price=20.0, stock=50, category_id=cat.id, is_active=True, cj_pid='PID3')
    db.session.add_all([p, p2, p3]); db.session.flush()
    db.session.add(ProductVariant(product_id=p3.id, cj_vid='VID1', variant_key='Rouge-M', color='Rouge', size='M', sku='V1', price=20.0, stock=5, active=True))
    o = Order(customer_email='Client@Example.com', shipping_first_name='Anne', shipping_last_name='B', shipping_address='1 rue', shipping_city='Lyon', shipping_postal_code='69000',
              status='shipped', payment_status='paid', total_price=30, subtotal=30, cj_tracking_number='LP123456789CN', cj_logistics_name='CJPacket')
    db.session.add(o); db.session.flush()
    db.session.add(OrderItem(order_id=o.id, product_id=p.id, quantity=1, price=30.0))
    db.session.commit()
    pid, pid2, pid3, onum, oid = p.id, p2.id, p3.id, o.order_number, o.id

c = app.test_client()
def get(url, code=200):
    r = c.get(url)
    assert r.status_code == code, (url, r.status_code, r.data[:300])
    return r.get_data(as_text=True)

# Menu
h = get('/')
for bad in ['Enchères', 'Petites Annonces', 'Abonnements', '>HOT<']:
    assert bad not in h, bad
assert 'Suivi de commande' in h and 'sort=newest' in h
for u in ['/encheres', '/annonces', '/abonnements', '/blog', '/promotions']:
    r = c.get(u); assert r.status_code == 301 and r.location.endswith('/products/'), (u, r.location)
assert c.get('/nouveautes').location.endswith('sort=newest')
assert c.get('/template-test').status_code == 404
# Pas de bandeau sans identifiants
assert 'consent-banner' not in h and 'window.mpsTrack = function () {}' in h
assert '<link rel="canonical" href="https://multiproshop.com/">' in h, re.findall('canonical[^>]*', h)
print('menu ok')

# Tri
h = get('/products/?sort=newest'); assert 'value="newest" selected' in h
h = get('/products/?sort=bestsellers'); assert h.index('LED Desk Lamp') < h.index('Motorcycle Phone Holder')
assert '(4.5)' not in h and 'addToWishlist' not in h
h = get(f'/products/?category={cat.id if False else 1}')
print('tri ok')

# Fiche produit
h = get(f'/products/{pid}')
assert '<title>Motorcycle Phone Holder | MultiProShop</title>' in h
assert 'shipping-country' in h and 'Acheter maintenant' in h and 'mobile-buy-bar' in h
ld = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', h, re.S).group(1))
assert ld['offers']['price'] == '30.00' and ld['offers']['availability'].endswith('InStock') and 'aggregateRating' not in ld
assert ld['description'].startswith('Support "solide"'), ld['description']
assert 'og:type" content="product"' in h and 'fetchpriority="high"' in h
assert "mpsTrack('view_item'" in h
print('fiche ok')

# Option obligatoire
r = c.post('/cart/add', json={'product_id': pid3, 'quantity': 1})
assert r.status_code == 400 and r.json['needs_variant'] and r.json['url'].endswith(f'/products/{pid3}')
r = c.post('/cart/add', data={'product_id': pid3, 'quantity': 1}); assert r.status_code == 302
print('variante ok')

# Recherche
with app.app_context():
    from services.search_service import get_search_service
    s = get_search_service()
    names = lambda q: [p.name for p in s.search_products(q)['products']]
    assert names('lampe') == ['LED Desk Lamp'], names('lampe')
    assert names('support téléphone') == ['Motorcycle Phone Holder'], names('support téléphone')
    assert names('lampe moto') == []
    assert names('vélo') == ['Motorcycle Phone Holder']  # description (accent conservé) ou "bike" non présent
    f = s.get_facets('lampe'); assert f['success'] and f['categories'][0]['count'] == 1, f
    f = s.get_facets(None); assert f['categories'][0]['count'] == 3, f
r = c.get('/search/api/suggestions?q=lamp')
assert r.json['products'][0]['url'] == f'/products/{pid2}', r.json
h = get('/search/?q=lampe'); assert 'LED Desk Lamp' in h and 'noindex' in h
h = get('/'); assert 'searchSuggestions' in h
print('recherche ok')

# Panier : progression + suggestions
c.post('/cart/add', json={'product_id': pid, 'quantity': 1})
h = get('/cart/')
assert 'free-shipping-progress' in h and 'width: 60%' in h and 'Complétez votre panier' in h
assert 'LED Desk Lamp' in h and 'Dress with variants' not in h
print('panier ok')

# Suivi de commande
h = get('/suivi-commande'); assert 'Retrouver ma commande' in h and 'noindex' in h
r = c.post('/suivi-commande', data={'order_number': onum.lower(), 'email': 'client@example.com '})
h = r.get_data(as_text=True); assert 'LP123456789CN' in h and '17track' in h and 'CJPacket' in h
r = c.post('/suivi-commande', data={'order_number': onum, 'email': 'autre@example.com'})
h = r.get_data(as_text=True); assert 'LP123456789CN' not in h and 'Aucune commande' in h
print('suivi ok')

# FAQ et e-mails
h = get('/faq'); assert 'offres exclusives' not in h and 'temps réel' not in h and '/suivi-commande' in h
with app.test_request_context():
    from flask import render_template
    with app.app_context():
        o = db.session.get(Order, oid)
        for t in ['emails/order_shipped.html', 'emails/order_delivered.html', 'emails/order_confirmation.html']:
            out = render_template(t, order=o)
            assert 'multiproshop.local' not in out and '2-5 jours' not in out, t
            assert 'https://multiproshop.com/suivi-commande' in out, t
        assert 'LP123456789CN' in render_template('emails/order_shipped.html', order=o)
print('emails ok')

# Analytique activée : bandeau, refus aussi visible, événements
app.config['ANALYTICS'] = {'ga4': 'G-TEST123', 'meta': '', 'tiktok': ''}
h = get('/about')
assert 'consent-banner' in h and 'Tout refuser' in h and '"ga4": "G-TEST123"' in h and 'Gérer les cookies' in h
h = get('/privacy'); assert 'Google Analytics 4' in h and 'Pixel Meta' not in h
print('analytics ok')
print('TOUT OK 2')
