import os, sys, json
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); sys.path.insert(0, ROOT); os.chdir(ROOT)
os.environ.pop('INES_API_KEY', None)
import app as appmod
from extensions import db, cache
app = appmod.create_app('testing'); appmod.app = app
from models.category import Category
from models.product import Product
from models.product_variant import ProductVariant
from models.user import User
from models.role import Role
with app.app_context():
    db.drop_all(); db.create_all(); cache.clear()
    c = Category(name='Animalerie', slug='a', level=1, is_active=True, visible=True); db.session.add(c); db.session.flush()
    p = Product(name='Gourde inox', slug='g', sku='S1', price=19.9, cost_price=5.0, stock=5, category_id=c.id, is_active=True, cj_pid='P1',
                description='Texte FR', image_url='https://img/propre.jpg', images='["https://img/propre.jpg"]'); db.session.add(p); db.session.flush()
    db.session.add(ProductVariant(product_id=p.id, cj_vid='V1', variant_key='Lot gourde verte', price=19.9, stock=3, image_url='https://img/propre.jpg', active=True))
    db.session.add(ProductVariant(product_id=p.id, cj_vid='V2', variant_key='Set12', price=19.9, stock=3, active=False))
    ra = Role(name='admin'); rc = Role(name='customer'); db.session.add_all([ra, rc]); db.session.flush()
    a = User(username='boss', email='b@x.com', role_id=ra.id); a.set_password('pw123456')
    u = User(username='client', email='c@x.com', role_id=rc.id); u.set_password('pw123456')
    db.session.add_all([a, u]); db.session.commit(); pid = p.id
    uid, aid = u.id, a.id

def client_as(user_id):
    cl = app.test_client()
    if user_id:
        with cl.session_transaction() as s: s['_user_id'] = str(user_id); s['_fresh'] = True
    return cl
paths = [('get', '/admin/'), ('get', '/admin/celery/'), ('post', '/admin/api/cj/enrich/P1'), ('get', '/admin/pricing/'), ('post', '/admin/api/sync/batch/1')]
anon, cust, adm = client_as(None), client_as(uid), client_as(aid)
for m, path in paths:
    r = getattr(anon, m)(path); assert r.status_code in (301, 302) and '/auth/' in r.headers['Location'], (path, r.status_code, r.headers.get('Location'))
    r = getattr(cust, m)(path); assert r.status_code == 404, (path, r.status_code, r.headers.get("Location"))
print('anonyme redirigé, client refusé (404) sur /admin : OK')
assert adm.get('/admin/').status_code == 200
assert anon.get('/').status_code == 200 and cust.get('/').status_code == 200
print('admin et pages publiques : OK')

# Synchro variantes : ne touche ni au prix, ni à l'image, ni au libellé, ni à l'état
import tasks.variant_sync_tasks as vt
class FakeApi:
    def __init__(self, *a, **k): pass
    def get_product_variants(self, pid):
        return {'data': [{'vid': 'V1', 'variantKey': 'Green', 'variantSellPrice': 3.2, 'variantImage': 'https://img/logo.jpg', 'variantStock': 40, 'variantSku': 'X'},
                {'vid': 'V2', 'variantKey': 'Set12', 'variantSellPrice': 3.0, 'variantImage': 'https://img/logo.jpg', 'variantStock': 40},
                {'vid': 'V3', 'variantKey': 'New', 'variantSellPrice': 2.0, 'variantImage': 'https://img/n.jpg', 'variantStock': 9}]}
    get_product_variants_list = get_product_variants
import inspect; src = inspect.getsource(vt.sync_product_variants)
vt.CJDropshippingApiOptimized = FakeApi
r = vt.sync_product_variants.run(pid)
print(r)
with app.app_context():
    v1 = ProductVariant.query.filter_by(cj_vid='V1').first(); v2 = ProductVariant.query.filter_by(cj_vid='V2').first(); v3 = ProductVariant.query.filter_by(cj_vid='V3').first()
    assert (v1.price, v1.image_url, v1.variant_key, v1.active, v1.stock) == (19.9, 'https://img/propre.jpg', 'Lot gourde verte', True, 40), v1.to_dict()
    assert v2.active is False and v2.stock == 40
    assert v3 and v3.price is None and v3.active is False, v3.to_dict()
print('synchro variantes (tâche) : prix, image, libellé et état conservés, nouvelle variante inactive OK')

from services.cj_variant_sync_service import CjVariantSyncService
class FakeApi2:
    def get_product_details(self, pid):
        return {'name': 'Dog bottle', 'description': 'EN', 'image': 'https://img/logo.jpg', 'images': ['https://img/logo.jpg'],
                'variants': [{'vid': 'V2', 'key': 'Set12', 'price': 3.0, 'stock': 7, 'image': 'https://img/logo.jpg'}]}
with app.app_context():
    res = CjVariantSyncService(FakeApi2()).sync_product_variants(pid); print(res)
    v2 = ProductVariant.query.filter_by(cj_vid='V2').first()
    assert v2.active is False and v2.price == 19.9 and v2.image_url != 'https://img/logo.jpg', v2.to_dict()
print('synchro variantes (service) : variante désactivée reste désactivée OK')
