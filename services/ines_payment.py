"""
Paiement des commandes par le Stripe d'INES (même circuit que Digita).

Les clés Stripe ne vivent que dans INES (/admin/integrations) : la boutique crée et relit ses
sessions Checkout via /api/v1/external/stripe/… avec sa clé API INES (compte administrateur).
Le webhook Stripe arrive à INES, pas ici : une commande est validée au retour du client sur
/cart/payment-success, et toutes les 15 minutes par la tâche reconcile_pending_orders pour un
client qui aurait fermé l'onglet avant ce retour.
"""
import logging
import os
from datetime import datetime, timedelta

import requests

from extensions import db

logger = logging.getLogger(__name__)

SITE = 'multiproshop'


class PaymentError(Exception):
    pass


def _url(path):
    return os.getenv('INES_API_URL', 'http://ines-backend:8000').rstrip('/') + '/api/v1/external/stripe' + path


def _headers():
    return {'Authorization': 'Bearer ' + os.getenv('INES_API_KEY', '')}


def enabled():
    return bool(os.getenv('INES_API_KEY'))


def _call(method, path, json=None):
    try:
        r = requests.request(method, _url(path), json=json, headers=_headers(), timeout=30)
    except requests.RequestException as e:
        raise PaymentError(str(e)) from e
    body = r.json() if r.content else {}
    if r.status_code >= 400:
        raise PaymentError(body.get('detail') or f'HTTP {r.status_code}')
    return body


def cents(amount):
    return int(round(amount * 100))


def create_checkout(order, success_url, cancel_url):
    """Session Checkout pour une commande en attente : les montants viennent de la commande
    (prix TTC enregistrés + livraison), jamais du navigateur. Renvoie {'id', 'url'}."""
    line_items = []
    for item in order.order_items:
        name = item.product.name if item.product else f'Produit {item.product_id}'
        if item.variant:
            details = ' / '.join(v for v in (item.variant.color, item.variant.size) if v)
            if details:
                name = f'{name} ({details})'
        product_data = {'name': name[:250]}
        if item.product and item.product.image_url and item.product.image_url.startswith('https://'):
            product_data['images'] = [item.product.image_url]
        line_items.append({
            'price_data': {'currency': 'eur', 'product_data': product_data, 'unit_amount': cents(item.price)},
            'quantity': item.quantity,
        })
    if order.shipping_cost > 0:
        line_items.append({
            'price_data': {'currency': 'eur', 'product_data': {'name': f'Livraison ({order.shipping_method})'},
                           'unit_amount': cents(order.shipping_cost)},
            'quantity': 1,
        })

    session = _call('POST', '/checkout-sessions', {'site': SITE, 'params': {
        'line_items': line_items,
        'mode': 'payment',
        'success_url': success_url + '?session_id={CHECKOUT_SESSION_ID}',
        'cancel_url': cancel_url,
        'client_reference_id': str(order.id),
        'customer_email': order.customer_email,
        'locale': 'fr',
        'metadata': {'order_id': order.id, 'order_number': order.order_number},
    }})
    order.stripe_session_id = session['id']
    db.session.commit()
    return session


def get_session(session_id):
    return _call('GET', f'/checkout-sessions/{session_id}')


def fulfill(order_id, session):
    """Valide une commande payée, une seule fois même si le retour client et la tâche de
    rattrapage arrivent ensemble : stock, e-mail de confirmation, commande CJ.
    Renvoie True si la commande vient d'être validée."""
    from models.order import Order

    order = Order.query.filter_by(id=order_id).with_for_update().first()
    if not order or order.payment_status == 'paid':
        db.session.rollback()
        return False
    if session.get('payment_status') != 'paid' or session.get('amount_total') != cents(order.total_price):
        db.session.rollback()
        if session.get('payment_status') == 'paid':
            logger.error("Montant payé %s ≠ commande %s (%s)", session.get('amount_total'), order.order_number,
                         cents(order.total_price))
        return False

    order.payment_status = 'paid'
    order.status = 'paid'
    order.paid_at = datetime.utcnow()
    for item in order.order_items:
        if item.variant:
            item.variant.stock = max(0, (item.variant.stock or 0) - item.quantity)
        elif item.product:
            item.product.stock = max(0, (item.product.stock or 0) - item.quantity)
    db.session.commit()
    logger.info("Commande %s payée (%s)", order.order_number, session.get('id'))

    try:
        from utils.email import send_order_confirmation_email
        send_order_confirmation_email(order)
    except Exception as e:  # noqa: BLE001 — un e-mail raté ne doit pas annuler la commande
        logger.error("E-mail de confirmation non envoyé pour %s : %s", order.order_number, e)

    try:
        from models.api_provider import ApiProvider
        from services.api_providers.cj_dropshipping_optimized import CJDropshippingProvider
        from services.cj_order_service import CjOrderService

        provider = ApiProvider.query.filter_by(name='CJ Dropshipping', active=True).first()
        if provider:
            result = CjOrderService(CJDropshippingProvider(provider)).create_cj_order(order.id)
            if not result.get('success'):
                logger.error("Commande CJ non créée pour %s : %s", order.order_number, result.get('message'))
    except Exception as e:  # noqa: BLE001 — la commande reste payée, à passer à la main sur CJ
        logger.error("Commande CJ non créée pour %s : %s", order.order_number, e)
    return True


def reconcile_pending_orders(max_age_hours=48):
    """Commandes en attente avec une session Checkout : validées si payées, annulées si la
    session a expiré (Stripe les fait expirer au bout de 24 h)."""
    from models.order import Order

    since = datetime.utcnow() - timedelta(hours=max_age_hours)
    pending = Order.query.filter(Order.payment_status == 'pending', Order.stripe_session_id.isnot(None),
                                 Order.created_at >= since).all()
    stats = {'checked': 0, 'paid': 0, 'cancelled': 0}
    for order in pending:
        stats['checked'] += 1
        try:
            session = get_session(order.stripe_session_id)
        except PaymentError as e:
            logger.warning("Session %s illisible : %s", order.stripe_session_id, e)
            continue
        if session.get('payment_status') == 'paid':
            stats['paid'] += fulfill(order.id, session)
        elif session.get('status') == 'expired':
            order.status = 'cancelled'
            order.payment_status = 'failed'
            db.session.commit()
            stats['cancelled'] += 1
    return stats
