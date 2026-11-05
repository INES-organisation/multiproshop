"""API partenaires (/api/partner) : catalogue public, commandes payées sur le site partenaire."""
import pytest

from extensions import db
from models.order import Order
from models.product import Product

TOKEN = 'x' * 32
AUTH = {'Authorization': f'Bearer {TOKEN}'}
CUSTOMER = {'first_name': 'Marie', 'last_name': 'Payet', 'email': 'Marie@Example.re', 'phone': '0692000000',
            'address': '1 rue de la Plage', 'city': 'Saint-Pierre', 'postal_code': '97410'}
METHODS = [{'code': 'STANDARD', 'name': 'Standard', 'price': 4.9, 'delivery_time': '10-20 jours'}]


@pytest.fixture(autouse=True)
def partner(monkeypatch, app):
    monkeypatch.setenv('PARTNER_TOKEN_TONYALPHA', TOKEN)
    from routes import partner_api
    monkeypatch.setattr(partner_api, '_shipping_methods', lambda items, country, subtotal: METHODS)
    with app.app_context():
        for p in Product.query.all():
            p.published = p.is_active
        db.session.commit()


@pytest.fixture
def payment(monkeypatch):
    from services import ines_payment
    calls = {}
    monkeypatch.setattr(ines_payment, 'enabled', lambda: True)

    def checkout(order, success_url, cancel_url):
        order.stripe_session_id = 'cs_test_1'
        db.session.commit()
        calls['checkout'] = (order.order_number, success_url)
        return {'id': 'cs_test_1', 'url': 'https://checkout.stripe.test/cs_test_1'}
    monkeypatch.setattr(ines_payment, 'create_checkout', checkout)
    return calls


def _product_id(app, name):
    with app.app_context():
        return Product.query.filter_by(name=name).first().id


def test_catalogue_public_and_published_only(client):
    data = client.get('/api/partner/catalogue').get_json()
    names = {p['name'] for p in data['products']}
    assert names == {'iPhone 13', 'T-Shirt'}
    assert data['total'] == 2 and {c['name'] for c in data['categories']} == {'Électronique', 'Vêtements'}
    assert client.get('/api/partner/catalogue?q=shirt').get_json()['total'] == 1


def test_product_detail(client, app):
    pid = _product_id(app, 'T-Shirt')
    assert client.get(f'/api/partner/products/{pid}').get_json()['variants'] == []
    assert client.get(f'/api/partner/products/{_product_id(app, "Produit inactif")}').status_code == 404


def test_token_required(client, app):
    body = {'items': [{'product_id': _product_id(app, 'T-Shirt'), 'quantity': 1}], 'country': 'FR'}
    assert client.post('/api/partner/shipping', json=body).status_code == 401
    assert client.post('/api/partner/shipping', json=body, headers={'Authorization': 'Bearer faux'}).status_code == 401
    r = client.post('/api/partner/shipping', json=body, headers=AUTH)
    assert r.status_code == 200 and r.get_json()['subtotal'] == 19.99


def test_order_prices_come_from_database(client, app, payment):
    pid = _product_id(app, 'T-Shirt')
    r = client.post('/api/partner/orders', headers=AUTH, json={
        'items': [{'product_id': pid, 'quantity': 2, 'price': 0.01}], 'country': 'FR', 'customer': CUSTOMER,
        'shipping_method': 'STANDARD', 'success_url': 'https://tonyalpha80.com/magasin/merci',
        'cancel_url': 'https://tonyalpha80.com/magasin/panier'})
    assert r.status_code == 201, r.get_json()
    data = r.get_json()
    assert data['total'] == round(2 * 19.99 + 4.9, 2) and data['checkout_url'].startswith('https://checkout')
    with app.app_context():
        order = Order.query.filter_by(order_number=data['order_number']).one()
        assert order.customer_email == 'marie@example.re' and 'tonyalpha80.com' in order.admin_notes
        assert order.payment_status == 'pending'


def test_order_rejects_bad_input(client, app, payment):
    base = {'country': 'FR', 'customer': CUSTOMER, 'shipping_method': 'STANDARD',
            'success_url': 'https://tonyalpha80.com/merci', 'cancel_url': 'https://tonyalpha80.com/panier'}
    inactive = _product_id(app, 'Produit inactif')
    assert client.post('/api/partner/orders', headers=AUTH,
                       json={**base, 'items': [{'product_id': inactive, 'quantity': 1}]}).status_code == 400
    pid = _product_id(app, 'T-Shirt')
    assert client.post('/api/partner/orders', headers=AUTH,
                       json={**base, 'items': [{'product_id': pid, 'quantity': 999}]}).status_code == 400
    assert client.post('/api/partner/orders', headers=AUTH,
                       json={**base, 'items': [{'product_id': pid, 'quantity': 1}],
                             'shipping_method': 'INCONNUE'}).status_code == 409
    assert client.post('/api/partner/orders', headers=AUTH,
                       json={**base, 'items': [{'product_id': pid, 'quantity': 1}],
                             'customer': {**CUSTOMER, 'address': ''}}).status_code == 400


def test_confirm_and_list(client, app, payment, monkeypatch):
    from services import ines_payment
    pid = _product_id(app, 'T-Shirt')
    data = client.post('/api/partner/orders', headers=AUTH, json={
        'items': [{'product_id': pid, 'quantity': 1}], 'country': 'FR', 'customer': CUSTOMER,
        'shipping_method': 'STANDARD', 'success_url': 'https://tonyalpha80.com/merci',
        'cancel_url': 'https://tonyalpha80.com/panier'}).get_json()
    fulfilled = []
    monkeypatch.setattr(ines_payment, 'get_session', lambda sid: {'payment_status': 'paid'})

    def fulfill(order_id, session):
        order = Order.query.get(order_id)
        order.payment_status = order.status = 'paid'
        db.session.commit()
        fulfilled.append(order_id)
    monkeypatch.setattr(ines_payment, 'fulfill', fulfill)
    r = client.post('/api/partner/orders/confirm', headers=AUTH, json={'session_id': 'cs_test_1'})
    assert r.status_code == 200 and r.get_json()['payment_status'] == 'paid' and len(fulfilled) == 1
    # Deuxième retour : rien n'est refait.
    client.post('/api/partner/orders/confirm', headers=AUTH, json={'session_id': 'cs_test_1'})
    assert len(fulfilled) == 1
    assert client.post('/api/partner/orders/confirm', headers=AUTH, json={'session_id': 'autre'}).status_code == 404
    orders = client.get('/api/partner/orders?email=marie@example.re', headers=AUTH).get_json()['orders']
    assert [o['order_number'] for o in orders] == [data['order_number']]


def test_variant_without_stock_uses_product_stock(client, app):
    from models.product_variant import ProductVariant
    with app.app_context():
        p = Product.query.filter_by(name='T-Shirt').first()
        db.session.add(ProductVariant(product_id=p.id, cj_vid='V1', color='Noir', size='M', price=21.0, stock=0))
        db.session.commit()
        pid, vid = p.id, ProductVariant.query.first().id
    assert client.get(f'/api/partner/products/{pid}').get_json()['variants'][0]['stock'] == 50
    r = client.post('/api/partner/shipping', headers=AUTH, json={'items': [{'product_id': pid, 'variant_id': vid}]})
    assert r.status_code == 200 and r.get_json()['subtotal'] == 21.0
