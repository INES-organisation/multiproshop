"""Codes promo : validation et calcul de la remise, toujours côté serveur.

La remise est plafonnée pour que la vente ne passe jamais à perte : le sous-total remisé
couvre au moins le coût CJ des articles et les frais de carte (le port reste payé par le
client, ou offert seulement si la marge le permet, voir routes.cart._with_free_shipping)."""
import re
from datetime import datetime

from flask import current_app, session

SESSION_KEY = 'coupon_code'


def normalize(code):
    return re.sub(r'\s+', '', code or '').upper()[:40]


def find(code):
    from models.coupon import Coupon
    code = normalize(code)
    return Coupon.query.filter_by(code=code).first() if code else None


def _used_by(coupon, email):
    from models.order import Order
    if not email:
        return False
    return Order.query.filter(Order.coupon_code == coupon.code, Order.payment_status == 'paid',
                              Order.customer_email.ilike(email.strip())).first() is not None


def _max_discount(items, subtotal):
    """Remise maximale sans vendre à perte, ou None si un coût est inconnu"""
    from models.cart import cost_price
    cost = 0.0
    for item in items:
        unit = cost_price(item['product'], item.get('variant'))
        if not unit:
            return None
        cost += unit * item['quantity']
    rate, fixed = current_app.config['CARD_FEE_RATE'], current_app.config['CARD_FEE_FIXED']
    # sous-total remisé S tel que S - coût - (S x taux + fixe) >= 0
    floor = (cost + fixed) / (1 - rate)
    return max(0.0, round(subtotal - floor, 2))


def evaluate(coupon, items, subtotal, email=None):
    """{'code', 'discount', 'free_shipping', 'capped', 'error'} pour ce panier"""
    from models.cart import admin_cost_mode
    result = {'code': coupon.code if coupon else None, 'discount': 0.0, 'free_shipping': False,
              'capped': False, 'error': None, 'label': coupon.label() if coupon else ''}
    if coupon is None:
        result['error'] = "Ce code promo n'existe pas."
        return result
    if admin_cost_mode():
        result['error'] = 'Les codes promo ne s\'appliquent pas aux commandes au prix coûtant.'
        return result
    status = coupon.status(datetime.utcnow())
    if status != 'actif':
        result['error'] = {'désactivé': "Ce code promo n'est plus valable.", 'à venir': "Ce code promo n'est pas encore valable.",
                           'expiré': 'Ce code promo a expiré.', 'épuisé': 'Ce code promo a déjà été utilisé au maximum.'}[status]
        return result
    if subtotal < (coupon.min_subtotal or 0):
        result['error'] = 'Ce code est valable dès %.2f € d\'achat.' % coupon.min_subtotal
        return result
    if coupon.once_per_email and _used_by(coupon, email):
        result['error'] = 'Ce code a déjà été utilisé avec cette adresse e-mail.'
        return result
    if coupon.kind == 'shipping':
        result['free_shipping'] = True
        return result
    wanted = subtotal * coupon.value / 100 if coupon.kind == 'percent' else coupon.value
    wanted = round(min(max(wanted, 0), subtotal), 2)
    ceiling = _max_discount(items, subtotal)
    if ceiling is None:
        result['error'] = "Ce code ne peut pas s'appliquer à ce panier."
        return result
    if wanted > ceiling:
        wanted, result['capped'] = ceiling, True
    if wanted <= 0:
        result['error'] = "Ce code ne peut pas s'appliquer à ce panier."
        return result
    result['discount'] = wanted
    return result


def current(items, subtotal, email=None):
    """Code enregistré dans la session pour ce panier (None si aucun ou plus valable)"""
    code = session.get(SESSION_KEY)
    if not code:
        return None
    result = evaluate(find(code), items, subtotal, email)
    if result['error']:
        return None
    return result
