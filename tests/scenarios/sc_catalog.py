import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); sys.path.insert(0, ROOT); os.chdir(ROOT)
import app as appmod
from extensions import db
app = appmod.create_app('testing'); appmod.app = app
from models.category import Category
from models.product import Product
from routes.api_products import clean_projects

assert clean_projects(' TonyAlpha, digita ,, x y, digita') == 'digita,tonyalpha'
with app.app_context():
    db.drop_all(); db.create_all()
    c = Category(name='Déco', slug='deco'); db.session.add(c); db.session.flush()
    for i, (proj, active) in enumerate([('tonyalpha,digita', True), ('digita', True), ('tonyalpha', False), (None, True), ('tonyalpha2', True)]):
        db.session.add(Product(name=f'P{i}', slug=f'p{i}', price=10, stock=1, category_id=c.id, is_active=active, projects=proj))
    db.session.commit()
cl = app.test_client()
res = cl.get('/api/catalog/tonyalpha'); r = res.get_json()
assert res.headers['Access-Control-Allow-Origin'] == '*'
assert [p['name'] for p in r['products']] == ['P0'], r  # actif seulement, pas « tonyalpha2 »
assert r['products'][0]['url'].endswith('/products/1')
assert {p['name'] for p in cl.get('/api/catalog/digita').get_json()['products']} == {'P0', 'P1'}
assert cl.get('/api/catalog/BAD..').status_code in (400, 404)
print('catalogue par projet OK')
