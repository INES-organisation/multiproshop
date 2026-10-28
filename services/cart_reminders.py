"""
Relances de panier abandonné, envoyées par INES (Brevo).

Le client saisit son e-mail au paiement → remember() garde le panier. Une tâche Celery
(tasks.cart_reminder_tasks) appelle send_due() : 1 h, 24 h puis 72 h après la dernière
activité, tant qu'aucune commande payée n'existe pour cet e-mail et que le client ne s'est
pas désinscrit.
"""
from datetime import datetime, timedelta
import json
import logging
import re

from flask import current_app, render_template

from extensions import db
from models.cart_reminder import CartReminder

logger = logging.getLogger(__name__)

SCHEDULE = (timedelta(hours=1), timedelta(hours=24), timedelta(hours=72))
SUBJECTS = (
    'Votre panier vous attend',
    'Toujours partant ? Votre panier est gardé',
    'Dernier rappel pour votre panier',
)
EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[a-z]{2,}$', re.I)


def remember(email, cart_items, token=None):
    """Enregistre (ou met à jour) la relance du navigateur ; renvoie son jeton, ou None"""
    email = (email or '').strip().lower()
    if not EMAIL_RE.match(email) or not cart_items:
        return None
    reminder = CartReminder.query.filter_by(token=token).first() if token else None
    if not reminder or reminder.completed_at or reminder.stopped_at:
        reminder = CartReminder(email=email)
        db.session.add(reminder)
    reminder.email = email
    reminder.items = json.dumps(cart_items)
    reminder.updated_at = datetime.utcnow()
    reminder.steps_sent = 0
    db.session.commit()
    return reminder.token


def stop(token):
    reminder = CartReminder.query.filter_by(token=token).first()
    if reminder and not reminder.stopped_at:
        reminder.stopped_at = datetime.utcnow()
        db.session.commit()
    return reminder


def _paid_since(reminder):
    from models.order import Order
    return Order.query.filter(
        db.func.lower(Order.customer_email) == reminder.email,
        Order.payment_status == 'paid',
        Order.created_at >= reminder.created_at,
    ).first() is not None


def _cart_lines(reminder):
    from models.product import Product
    from models.product_variant import ProductVariant
    lines = []
    for item in reminder.get_items().values():
        product = db.session.get(Product, item['product_id']) if isinstance(item, dict) else None
        if not product or not product.is_active:
            continue
        variant = db.session.get(ProductVariant, item['variant_id']) if item.get('variant_id') else None
        price = variant.price if variant and variant.price else product.price
        lines.append({'product': product, 'variant': variant, 'quantity': item['quantity'], 'price': price})
    return lines


def send_due(now=None):
    """Envoie les relances arrivées à échéance ; renvoie le nombre d'e-mails envoyés"""
    from utils.email import _send_via_ines

    now = now or datetime.utcnow()
    sent = 0
    # Conservation annoncée dans la politique de confidentialité : 30 jours
    CartReminder.query.filter(CartReminder.created_at < now - timedelta(days=30)).delete()
    active = CartReminder.query.filter(
        CartReminder.completed_at.is_(None),
        CartReminder.stopped_at.is_(None),
        CartReminder.steps_sent < len(SCHEDULE),
        CartReminder.updated_at <= now - SCHEDULE[0],
    ).all()
    site_url = current_app.config['SITE_URL']
    for reminder in active:
        if now - reminder.updated_at < SCHEDULE[reminder.steps_sent]:
            continue
        if _paid_since(reminder):
            reminder.completed_at = now
            continue
        lines = _cart_lines(reminder)
        if not lines:
            reminder.stopped_at = now
            continue
        step = reminder.steps_sent
        html = render_template('emails/cart_reminder.html', step=step, lines=lines,
                               total=sum(l['price'] * l['quantity'] for l in lines),
                               restore_url=f'{site_url}/cart/reprendre/{reminder.token}',
                               stop_url=f'{site_url}/cart/relances/stop/{reminder.token}')
        if _send_via_ines(reminder.email, SUBJECTS[step], html):
            reminder.steps_sent = step + 1
            reminder.last_sent_at = now
            sent += 1
    db.session.commit()
    if sent:
        logger.info("[Relances] %s e-mail(s) de panier abandonné envoyé(s)", sent)
    return sent
