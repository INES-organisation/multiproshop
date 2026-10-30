"""
Demandes d'avis, envoyées par INES (Brevo) une semaine après la livraison.

Une tâche Celery (tasks.review_request_tasks) appelle send_due() : pour chaque commande payée
livrée depuis 7 jours (ou expédiée depuis 21 jours sans confirmation de livraison), un seul
e-mail avec un lien personnel vers /avis/<jeton>. Les avis déposés sont marqués « achat
vérifié » et publiés tels quels (mention L111-7-2 sur la fiche produit).
"""
from datetime import datetime, timedelta
import json
import logging

from flask import current_app, render_template

from extensions import db
from models.order import Order
from models.product_review import ProductReview
from models.review_request import ReviewRequest

logger = logging.getLogger(__name__)

AFTER_DELIVERY = timedelta(days=7)
AFTER_SHIPPING = timedelta(days=21)  # livraison jamais confirmée par le transporteur
MAX_AGE = timedelta(days=90)         # pas de demande pour une commande trop ancienne
SUBJECT = 'Votre avis sur votre commande MultiProShop'


def author_name(order):
    """« Prénom N. » : jamais le nom complet du client"""
    first = (order.shipping_first_name or '').strip().title() or 'Client'
    last = (order.shipping_last_name or '').strip()
    return f'{first} {last[0].upper()}.' if last else first


def reviewable_items(request_):
    """Articles de la commande pas encore notés, un par produit"""
    from models.order import OrderItem
    reviewed = request_.reviewed_ids()
    items, seen = [], set()
    for item in OrderItem.query.filter_by(order_id=request_.order_id):
        if item.product and item.product_id not in reviewed and item.product_id not in seen:
            seen.add(item.product_id)
            items.append(item)
    return items


def send_due(now=None, limit=50):
    """Envoie les demandes d'avis arrivées à échéance ; renvoie le nombre d'e-mails envoyés"""
    from utils.email import _send_via_ines

    now = now or datetime.utcnow()
    already = db.session.query(ReviewRequest.order_id)
    due = Order.query.filter(
        Order.payment_status == 'paid',
        Order.created_at >= now - MAX_AGE,
        ~Order.id.in_(already),
        db.or_(
            Order.delivered_at <= now - AFTER_DELIVERY,
            db.and_(Order.delivered_at.is_(None), Order.shipped_at <= now - AFTER_SHIPPING),
        ),
    ).limit(limit).all()
    site_url = current_app.config['SITE_URL']
    sent = 0
    for order in due:
        request_ = ReviewRequest(order_id=order.id)
        db.session.add(request_)
        db.session.flush()
        items = reviewable_items(request_)
        if not items:
            request_.completed_at = now
            continue
        html = render_template('emails/review_request.html', order=order, items=items,
                               review_url=f'{site_url}/avis/{request_.token}',
                               stop_url=f'{site_url}/avis/{request_.token}/non-merci')
        if _send_via_ines(order.customer_email, SUBJECT, html):
            request_.sent_at = now
            sent += 1
        else:
            db.session.delete(request_)  # nouvel essai au prochain passage
    db.session.commit()
    if sent:
        logger.info("[Avis] %s demande(s) d'avis envoyée(s)", sent)
    return sent


def save_reviews(request_, form):
    """Enregistre les notes du formulaire ; renvoie le nombre d'avis créés"""
    created = 0
    for item in reviewable_items(request_):
        try:
            rating = int(form.get(f'rating_{item.product_id}') or 0)
        except ValueError:
            rating = 0
        comment = (form.get(f'comment_{item.product_id}') or '').strip()[:2000]
        if not 1 <= rating <= 5:
            continue
        db.session.add(ProductReview(
            product_id=item.product_id,
            author_name=author_name(request_.order), rating=rating,
            title=(form.get(f'title_{item.product_id}') or '').strip()[:200] or None,
            comment=comment or '—', verified_purchase=True, is_approved=True,
            review_date=datetime.utcnow(),
        ))
        request_.reviewed = json.dumps(sorted(request_.reviewed_ids() | {item.product_id}))
        created += 1
    if created and not reviewable_items(request_):
        request_.completed_at = datetime.utcnow()
    db.session.commit()
    return created
