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
import routes.admin as adm
import services.shipping_service as ss
seen = []
class Fake:
    def get_products_v2(self, page=1, page_size=24, keyword=None, category_id=None):
        seen.append((keyword, category_id))
        return {'products': [{'pid': 'NEW1', 'name': 'Cordless Drill 21V', 'sku': 'CJD1', 'image': 'http://x/i.jpg', 'price': 20.0, 'stock': 500, 'category_id': 'c'},
                             {'pid': 'P1', 'name': 'Tree', 'sku': 'S1', 'image': '', 'price': 10.0, 'stock': 5, 'category_id': 'c'}], 'total_pages': 1}
    def get_product_details(self, pid):
        return {'pid': pid, 'name': 'Cordless Drill 21V', 'sku': 'CJD1', 'price': 20.0, 'suggested_price': 60, 'stock': 500, 'images': ['http://x/i.jpg'],
                'description': '<p>drill</p>', 'variants': [{'vid': 'VD1', 'key': 'Black', 'sku': 'CJD1-B', 'price': 20.0, 'stock': 500}]}
    def get_variant_inventory(self, vid): return [{'country': 'CN', 'total': 120}]
    def calculate_shipping(self, products, country, start_country='CN'):
        return [{'logisticName': 'CJPacket', 'logisticPrice': 8.0, 'logisticAging': '10-15'}] if country == 'FR' else []
adm._cj_api = lambda: Fake()
ss.ShippingService.__init__ = lambda self: setattr(self, 'cj_api', Fake())
with app.app_context():
    cat_id = Category.query.first().id
r = cl.get('/admin/cj-recherche?q=drill&category=%d' % cat_id); h = r.get_data(as_text=True)
assert r.status_code == 200 and 'Cordless Drill 21V' in h and 'Déjà en boutique' in h and '18.40 €' in h, h[-3000:]
r = cl.post('/admin/cj-recherche/port', json={'pid': 'NEW1'}).json
assert r['FR']['price'] == 7.36 and r['RE'] is False, r
r = cl.post('/admin/cj-recherche/importer', data={'pid': 'NEW1', 'category_id': cat_id, 'q': 'drill'})
assert r.status_code == 302 and '/products/edit/' in r.headers['Location'], (r.status_code, r.headers)
with app.app_context():
    p = Product.query.filter_by(cj_pid='NEW1').first()
    assert p and not p.is_active and p.published_at is None and p.cost_price == 18.4 and p.price > 18.4 and p.category_id == cat_id, p
    pid2 = p.id
    from models.product_variant import ProductVariant
    assert ProductVariant.query.filter_by(product_id=pid2, cj_vid='VD1').count() == 1
import services.publication as pub
pub._api = lambda: Fake()
r = cl.post(f'/admin/products/toggle-status/{pid2}')
with app.app_context():
    p = Product.query.get(pid2); assert not p.is_active and p.stock == 120, 'refus attendu : pas de livraison à La Réunion'
from extensions import cache
with app.app_context(): cache.clear()
Fake.calculate_shipping = lambda self, products, country, start_country='CN': [{'logisticName': 'CJPacket', 'logisticPrice': 8.0, 'logisticAging': '10-15'}]
r = cl.post(f'/admin/products/toggle-status/{pid2}')
with app.app_context():
    p = Product.query.get(pid2); assert p.is_active and p.published_at is not None and p.price == 36.9, p.price
anon = app.test_client()
assert anon.get('/admin/cj/products').status_code in (302, 401) and anon.get('/admin/cj-recherche?q=x').status_code in (302, 401)
with app.app_context():
    c = Category.query.get(cat_id); c.cj_category_id = 'CJCAT'; from extensions import db as _db; _db.session.commit()
r = cl.get('/admin/cj-recherche?category=%d' % cat_id); assert r.status_code == 200 and 'Cordless Drill 21V' in r.get_data(as_text=True)
assert seen[-1] == (None, 'CJCAT'), seen
with app.app_context():
    from models.api_provider import CategoryMapping
    from extensions import db as _db
    c2 = Category(name='Montres', slug='montres-x', level=2, parent_id=cat_id, is_active=True, visible=True); _db.session.add(c2); _db.session.flush()
    _db.session.add(CategoryMapping(provider_id=1, external_category_id='CJWATCH', external_category_name='Watches', mps_category_id=c2.id))
    _db.session.commit(); c2id = c2.id
r = cl.get('/admin/cj-recherche?category=%d' % c2id); assert r.status_code == 200 and seen[-1] == (None, 'CJWATCH'), seen[-1]
r = cl.get('/admin/cj-recherche?q=watch&category=%d' % c2id); assert seen[-1] == ('watch', 'CJWATCH'), seen[-1]
print('TOUT OK recherche CJ')
