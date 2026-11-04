"""E-mails : chaque modèle se rend et part dans la mise en page commune (logo, pied de page légal)."""
from datetime import datetime
from types import SimpleNamespace as NS

from flask import render_template

from utils import email as ue


def test_templates_render_inside_common_layout(app, monkeypatch):
    sent = []
    monkeypatch.setenv('INES_API_KEY', 'k')
    monkeypatch.setattr(ue.requests, 'post', lambda url, json, **kw: sent.append(json) or NS(raise_for_status=lambda: None))
    product = NS(name='Lampe', image_url='https://x/img.jpg')
    order = NS(order_number='ORD-1', shipping_first_name='Ana', shipping_last_name='B', created_at=datetime(2026, 11, 4),
               payment_status='paid', order_items=[NS(product=product, quantity=2, price=10.0)], subtotal=20.0,
               discount_amount=0, coupon_code=None, shipping_cost=4.9, shipping_method='Standard', total_price=24.9,
               shipping_address='1 rue', shipping_postal_code='97430', shipping_city='Le Tampon', shipping_country='FR',
               cj_tracking_number='TRK1', cj_logistics_name='CJ', customer_email='ana@test.re')
    with app.test_request_context():
        pages = {
            'order_confirmation': render_template('emails/order_confirmation.html', order=order),
            'order_shipped': render_template('emails/order_shipped.html', order=order, tracking_number=None),
            'order_delivered': render_template('emails/order_delivered.html', order=order),
            'reset_password': render_template('emails/reset_password.html', user=NS(username='ana'), link='https://l'),
            'cart_reminder': render_template('emails/cart_reminder.html', step=1, total=20.0, restore_url='https://r',
                                             stop_url='https://s', lines=[NS(product=product, variant=None, quantity=2, price=10.0)]),
            'review_request': render_template('emails/review_request.html', order=order, items=[NS(product=product)],
                                              review_url='https://v', stop_url='https://s'),
        }
    for name, html in pages.items():
        assert ue._send_via_ines('ana@test.re', f'Sujet {name} - MultiProShop', html, name)
    for body in sent:
        assert body['site'] == 'multiproshop' and body['template']
        assert 'logo-email.png' in body['html'] and 'SIREN' in body['html'] and body['html'].count('<body') == 1
    assert '>Sujet order_confirmation<' in sent[0]['html']  # titre repris du sujet, sans « - MultiProShop »
    assert ue.wrap('x', sent[0]['html']) == sent[0]['html']  # pas de double enveloppe
