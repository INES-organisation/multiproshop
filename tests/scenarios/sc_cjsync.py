import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); sys.path.insert(0, ROOT); os.chdir(ROOT)
os.environ.pop('INES_API_KEY', None)
import app as appmod
from extensions import db, cache
app = appmod.create_app('testing'); appmod.app = app
from models.category import Category
from models.product import Product
from models.user import User
from models.role import Role
import routes.admin_cj_sync as rs
seen = []
mode = {'v': 'ok'}
class Api:
    def get_products(self, page=1, page_size=20, filters=None):
        seen.append((filters or {}).get('categoryId'))
        if mode['v'] == 'err':
            return {'products': [], 'total': 0, 'page': page, 'error': 'Too Many Requests'}
        if page > 1:
            return {'products': [], 'total': 2, 'page': page, 'total_pages': 1}
        return {'products': [{'pid': 'NEW1', 'sku': 'N1', 'name': 'Hiking shoe', 'price': 12.0, 'suggested_price': 60, 'images': ['http://x/1.jpg'],
                              'category_id': 'CJ-HIKE'},
                             {'pid': 'OLD1', 'sku': 'O1', 'name': 'Old', 'price': 5.0, 'category_id': 'CJ-HIKE'}],
                'total': 2, 'page': 1, 'total_pages': 1}
rs.get_cj_api = lambda: Api()
with app.app_context():
    db.drop_all(); db.create_all(); cache.clear()
    top = Category(name='Sport', slug='s', level=1, is_active=True, visible=True, cj_category_id='CJ-SPORT'); db.session.add(top); db.session.flush()
    hike = Category(name='Hiking Shoes', slug='h', level=2, parent_id=top.id, is_active=True, visible=True, cj_category_id='CJ-HIKE'); db.session.add(hike)
    lone = Category(name='Divers', slug='d', level=1, is_active=True, visible=True); db.session.add(lone); db.session.flush()
    db.session.add(Product(name='Chaussure FR', slug='old', sku='O1', cj_pid='OLD1', price=29.9, stock=3, category_id=hike.id, is_active=True))
    ra = Role(name='admin'); db.session.add(ra); db.session.flush()
    a = User(username='boss', email='b@x.com', role_id=ra.id); a.set_password('pw123456'); db.session.add(a)
    db.session.commit(); hid, lid, aid = hike.id, lone.id, a.id
cl = app.test_client()
with cl.session_transaction() as s: s['_user_id'] = str(aid); s['_fresh'] = True
r = cl.post('/admin/api/cj/sync/products', json={'category_id': str(hid), 'limit': 100}).json
assert r['success'] and r['synced'] == 2 and r['created'] == 1 and 'brouillon' in r['message'], r
assert seen[0] == 'CJ-HIKE', seen
with app.app_context():
    n = Product.query.filter_by(cj_pid='NEW1').first(); o = Product.query.filter_by(cj_pid='OLD1').first()
    assert not n.is_active and not n.published and n.compare_price is None and n.price == 25.9, (n.is_active, n.compare_price, n.price)
    assert o.is_active and o.name == 'Chaussure FR' and o.price == 29.9
    assert db.session.get(Category, hid).product_count == 2 and Category.query.filter_by(cj_category_id='CJ-SPORT').first().product_count == 2
print('catégorie boutique -> id CJ, nouveaux en brouillon sans prix barré, compteurs OK')
seen.clear(); cl.post('/admin/api/cj/sync/products', json={'category_id': 'all'}); assert seen[0] is None, seen
r = cl.post('/admin/api/cj/sync/products', json={'category_id': str(lid)}); assert r.status_code == 400 and 'Divers' in r.json['message'], r.json
mode['v'] = 'err'
r = cl.post('/admin/api/cj/sync/products', json={'category_id': str(hid)}); assert r.status_code == 500 and 'Too Many' in r.json['message'], r.json
print('tout le catalogue, catégorie sans CJ, erreur CJ affichée OK')
