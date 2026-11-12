"""Boutiques et vitrines : création, produits (ajout, publication des brouillons, retrait), pause,
réglages publics lus par la boutique, seuil de livraison offerte et mention des commandes."""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); sys.path.insert(0, ROOT); os.chdir(ROOT)
os.environ.pop('INES_API_KEY', None)
os.environ['PARTNER_TOKEN_DIGITA'] = 'd' * 32
os.environ.pop('PARTNER_TOKEN_MAISON_ZEN', None)
import app as appmod
from extensions import db, cache
app = appmod.create_app('testing')
from models.category import Category
from models.product import Product
from models.role import Role
from models.storefront import Storefront, ensure_defaults
from models.user import User

with app.app_context():
    db.drop_all(); db.create_all(); cache.clear()
    ensure_defaults(); ensure_defaults()  # une seule fois chacune
    assert {s.slug: s.kind for s in Storefront.query} == {'serenis': 'boutique', 'tonyalpha': 'vitrine', 'digita': 'vitrine'}
    assert Storefront.query.filter_by(slug='tonyalpha').first().order_label == 'tonyalpha80.com (ALIAS)'
    c = Category(name='Studio', slug='st', level=1, is_active=True, visible=True); db.session.add(c); db.session.flush()
    ring = Product(name='Anneau lumineux', slug='ring', sku='R1', price=19.9, cost_price=6, stock=50, category_id=c.id,
                   is_active=False, published=True, projects='digita')  # brouillon, hors CJ : pas d'appel CJ
    mic = Product(name='Micro-cravate', slug='mic', sku='M1', price=14.9, cost_price=5, stock=50, category_id=c.id,
                  is_active=True, published=True, cj_pid='M1', projects='serenis')
    lamp = Product(name='Lampe de bureau', slug='lamp', sku='L1', price=24.9, cost_price=9, stock=50, category_id=c.id,
                   is_active=True, published=True, cj_pid='L1')
    db.session.add_all([ring, mic, lamp])
    r = Role(name='admin'); db.session.add(r); db.session.flush()
    u = User(username='boss', email='b@x.com', role_id=r.id); u.set_password('pw123456'); db.session.add(u)
    db.session.commit()
    ring_id, mic_id, lamp_id = ring.id, mic.id, lamp.id

pub = app.test_client()
assert pub.get('/admin/vitrines').status_code in (302, 401, 403)  # réservé aux admins
cl = app.test_client()
cl.post('/auth/admin-login', data={'username': 'boss', 'password': 'pw123456'})

h = cl.get('/admin/vitrines').get_data(as_text=True)
assert 'Sérénis' in h and 'ALIAS' in h and 'DIGITA' in h and '1 en brouillon' in h, h[-3000:]
print('liste OK')

# Catalogue de DIGITA : le brouillon n'y est pas ; on ajoute le micro et la lampe, puis on publie les brouillons
cat = lambda: {p['id'] for p in pub.get('/api/partner/catalogue?project=digita').get_json()['products']}
assert cat() == set()
cl.post('/admin/vitrines/digita/produits', data={'action': 'add', 'ids': [str(mic_id)], 'id_list': f'{lamp_id}'})
assert cat() == {mic_id, lamp_id}
with app.app_context():
    assert db.session.get(Product, mic_id).projects == 'digita,serenis'  # Sérénis garde le produit
cl.post('/admin/vitrines/digita/produits', data={'action': 'publish'})  # rien de coché : tous les brouillons
assert cat() == {mic_id, lamp_id, ring_id}
with app.app_context():
    ring = db.session.get(Product, ring_id)
    assert ring.is_active and ring.published_at is not None
cl.post('/admin/vitrines/digita/produits', data={'action': 'remove', 'ids': [str(lamp_id)]})
assert cat() == {mic_id, ring_id}
page = cl.get('/admin/vitrines/digita?q=Lampe').get_data(as_text=True)
assert 'Lampe de bureau' in page and 'Jeton de la vitrine : PARTNER_TOKEN_DIGITA' in page, page[-3000:]
print('produits OK')

# Réglages : seuil propre, pause, réglages publics
cl.post('/admin/vitrines/digita', data={'name': 'DIGITA', 'status': 'en_ligne', 'url': 'https://digita.buzz/boutique',
                                        'free_shipping_threshold': '49', 'color': '#7c3aed', 'delivery_days': '10-18'})
data = pub.get('/api/partner/catalogue?project=digita').get_json()
assert data['free_shipping']['threshold'] == 49, data['free_shipping']
info = pub.get('/api/partner/storefront/digita').get_json()
assert info['status'] == 'en_ligne' and info['delivery_days'] == '10-18' and info['free_shipping_threshold'] == 49, info
assert pub.get('/api/partner/storefront/inconnue').status_code == 404
r = cl.post('/admin/vitrines/digita', data={'name': 'DIGITA', 'status': 'en_ligne', 'color': 'violet', 'lots': '{pas du json'})
with app.app_context():
    assert Storefront.query.filter_by(slug='digita').first().color == '#7c3aed'  # erreur : rien n'est changé
cl.post('/admin/vitrines/digita', data={'name': 'DIGITA', 'status': 'pause'})
assert cat() == set()
assert pub.get(f'/api/partner/products/{mic_id}?project=digita').status_code == 404
assert pub.get(f'/api/partner/products/{mic_id}?project=serenis').status_code == 200  # les autres sites continuent
print('réglages et pause OK')

# Création d'une nouvelle boutique
assert cl.post('/admin/vitrines/nouvelle', data={'slug': 'ines', 'name': 'X', 'url': 'https://x.fr'}).status_code == 200
r = cl.post('/admin/vitrines/nouvelle', data={'slug': 'maison-zen', 'name': 'Maison Zen', 'kind': 'boutique',
                                              'url': 'https://zen.multiproshop.com'})
assert r.status_code == 302 and r.headers['Location'].endswith('/admin/vitrines/maison-zen'), r.status_code
page = cl.get('/admin/vitrines/maison-zen').get_data(as_text=True)
assert 'PARTNER_TOKEN_MAISON_ZEN' in page and 'maison-zen-web' in page and "Lots de l'accueil" in page
with app.app_context():
    zen = Storefront.query.filter_by(slug='maison-zen').first()
    assert zen.order_label == 'zen.multiproshop.com' and zen.status == 'preparation' and not zen.token_configured
    from routes.partner_api import site_label
    assert site_label('maison-zen') == 'zen.multiproshop.com' and site_label('serenis') == 'serenis.multiproshop.com'
print('création OK')
