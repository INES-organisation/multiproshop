import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); sys.path.insert(0, ROOT); os.chdir(ROOT)
os.environ.pop('INES_API_KEY', None)
import app as appmod
from extensions import db, cache
app = appmod.create_app('testing')
from models.category import Category
from models.cj_sourcing import CjSourcing
from models.user import User
from models.role import Role
from services.api_providers.cj_dropshipping_optimized import CJDropshippingApiOptimized as Api

# Client CJ : corps envoyé à product/sourcing/create et lecture de product/sourcing/queryList
calls = []
api = Api.__new__(Api)
api._make_request = lambda method, endpoint, **kw: calls.append((method, endpoint, kw)) or (
    {'result': True, 'data': {'cjSourcingId': '285', 'result': 'success'}} if endpoint.endswith('create')
    else {'result': True, 'data': [{'sourceId': '285', 'sourceStatus': '3', 'sourceStatusStr': 'Sourcing succeeded',
                                     'cjProductId': 'PID9', 'cjVariantSku': 'CJ1', 'failReasonStr': None}]})
assert api.create_sourcing('Lampe', 'https://x/i.jpg', 'https://aliexpress.com/item/1', 4.5) == {'id': '285'}
assert calls[0] == ('POST', 'product/sourcing/create', {'json': {'productName': 'Lampe', 'productImage': 'https://x/i.jpg',
                                                                  'productUrl': 'https://aliexpress.com/item/1', 'price': 4.5}}), calls
assert api.query_sourcing('285')['cjProductId'] == 'PID9'
assert calls[1][1:] == ('product/sourcing/queryList', {'params': {'sourceIds': '285'}})

with app.app_context():
    db.drop_all(); db.create_all(); cache.clear()
    db.session.add(Category(name='Maison', slug='m', level=1, is_active=True, visible=True))
    r = Role(name='admin'); db.session.add(r); db.session.flush()
    u = User(username='boss', email='b@x.com', role_id=r.id); u.set_password('pw123456'); db.session.add(u)
    db.session.commit()
cl = app.test_client()
cl.post('/auth/admin-login', data={'username': 'boss', 'password': 'pw123456'})
import routes.admin as adm
adm._cj_api = lambda: api

assert cl.post('/admin/cj-sourcing', data={'product_name': 'Lampe', 'product_image': 'javascript:x'}).status_code == 302
with app.app_context():
    assert CjSourcing.query.count() == 0  # image invalide : rien envoyé
cl.post('/admin/cj-sourcing', data={'product_name': 'Lampe', 'product_image': 'https://x/i.jpg',
                                     'product_url': 'https://aliexpress.com/item/1', 'price': '4.5'})
h = cl.get('/admin/cj-sourcing').get_data(as_text=True)
assert 'n° CJ 285' in h and 'En cours' in h, h[-2000:]
cl.post('/admin/cj-sourcing/actualiser')
h = cl.get('/admin/cj-sourcing').get_data(as_text=True)
assert 'Trouvé' in h and 'name="pid" value="PID9"' in h, h[-2000:]
with app.app_context():
    assert CjSourcing.query.one().found
print('sourcing CJ OK')
