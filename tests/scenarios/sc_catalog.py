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
        db.session.add(Product(name=f'P{i}', slug=f'p{i}', price=10, stock=1, category_id=c.id, is_active=active, published=True, projects=proj))
    db.session.commit()
cl = app.test_client()
url = '/api/partner/catalogue?project='
res = cl.get(url + 'tonyalpha'); r = res.get_json()
assert res.headers['Access-Control-Allow-Origin'] == '*'
assert [p['name'] for p in r['products']] == ['P0'], r  # actif seulement, pas « tonyalpha2 »
assert r['categories'] == [{'id': 1, 'name': 'Déco', 'count': 1}], r  # comptes limités à la vitrine
assert {p['name'] for p in cl.get(url + 'digita').get_json()['products']} == {'P0', 'P1'}
assert cl.get(url + 'BAD..').status_code == 400
assert cl.get('/api/partner/catalogue').get_json()['total'] == 4  # sans projet : tout le catalogue publié
print('catalogue par projet OK')

# Chiffres pour les moniteurs d'INES : jeton INES seulement
os.environ['PARTNER_TOKEN_INES'] = 'i' * 32; os.environ['PARTNER_TOKEN_TONYALPHA'] = 't' * 32
from datetime import datetime
from models.order import Order
with app.app_context():
    db.session.add(Order(order_number='A1', customer_email='a@b.c', shipping_first_name='A', shipping_last_name='B',
                         shipping_address='x', shipping_city='y', shipping_postal_code='1', subtotal=20, total_price=25,
                         payment_status='paid', status='paid', paid_at=datetime.utcnow()))
    db.session.commit()
assert cl.get('/api/partner/stats', headers={'Authorization': 'Bearer ' + 't' * 32}).status_code == 403
s = cl.get('/api/partner/stats', headers={'Authorization': 'Bearer ' + 'i' * 32}).get_json()
assert s['sales']['week']['orders'] == 1 and s['sales']['week']['revenue'] == 25, s
assert s['paid_orders_by_site'] == {'multiproshop': 1, 'tonyalpha': 0}, s
assert s['to_send_to_cj'] == 1 and s['products_online'] == 4, s
print('chiffres INES OK')
