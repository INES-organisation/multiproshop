"""Inscription à la newsletter : un code de bienvenue -10 % personnel, valable 30 jours, envoyé par e-mail"""
import re
import secrets
from datetime import datetime, timedelta

from extensions import db

DISCOUNT = 10          # %
MIN_SUBTOTAL = 20.0    # € de produits
VALID_DAYS = 30
EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[a-z]{2,}$', re.I)


def _new_code():
    from models.coupon import Coupon
    while True:
        code = 'BIENVENUE-' + ''.join(secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(6))
        if not Coupon.query.filter_by(code=code).first():
            return code


def subscribe(email, source='site'):
    """Inscrit l'adresse (ou la réinscrit) et renvoie (abonné, coupon, nouveau ?). ValueError si l'adresse est invalide."""
    from models.coupon import Coupon
    from models.newsletter import NewsletterSubscriber
    email = (email or '').strip().lower()
    if not EMAIL_RE.match(email) or len(email) > 255:
        raise ValueError('Adresse e-mail invalide.')
    sub = NewsletterSubscriber.query.filter_by(email=email).first()
    created = sub is None
    if created:
        sub = NewsletterSubscriber(email=email, source=source)
        db.session.add(sub)
    sub.unsubscribed_at = None
    coupon = Coupon.query.filter_by(code=sub.coupon_code).first() if sub.coupon_code else None
    if coupon is None:
        coupon = Coupon(code=_new_code(), kind='percent', value=DISCOUNT, min_subtotal=MIN_SUBTOTAL,
                        ends_at=datetime.utcnow() + timedelta(days=VALID_DAYS), max_uses=1, once_per_email=True,
                        active=True, note=f'newsletter {email}'[:200])
        db.session.add(coupon)
        sub.coupon_code = coupon.code
    db.session.commit()
    return sub, coupon, created


def send_welcome(sub, coupon, base_url, shop_name='MultiProShop', shop_url=None):
    """base_url : adresse publique de MPS (lien de désinscription). shop_name / shop_url : la boutique où
    l'abonné s'est inscrit (une vitrine comme Sérénis), MPS par défaut."""
    from markupsafe import escape
    from utils.email import send_email
    shop_name = escape(shop_name)
    shop_url = shop_url or f'{base_url}/products/'
    end = coupon.ends_at.strftime('%d/%m/%Y') if coupon.ends_at else ''
    used = coupon.uses and coupon.max_uses and coupon.uses >= coupon.max_uses
    unsubscribe = f'{base_url}/newsletter/desinscription/{sub.token}'
    body = f"""
<p>Bonjour,</p>
<p>Merci pour votre inscription à la newsletter {shop_name}.</p>
{'' if used else f'''<p>Voici votre code de bienvenue : <strong style="font-size:18px">{coupon.code}</strong><br>
-{int(coupon.value)} % sur votre première commande dès {coupon.min_subtotal:.0f} € d'articles, valable jusqu'au {end}.
À saisir dans le panier, au moment du paiement.</p>'''}
<p><a href="{shop_url}">Découvrir la boutique</a></p>
<p style="color:#888;font-size:12px">Vous recevez cet e-mail car vous vous êtes inscrit sur {shop_name}.
<a href="{unsubscribe}">Se désinscrire</a></p>"""
    send_email(subject=f'Votre code de bienvenue {shop_name}', to=sub.email, html=body)


def unsubscribe(token):
    from models.newsletter import NewsletterSubscriber
    sub = NewsletterSubscriber.query.filter_by(token=token).first()
    if sub and not sub.unsubscribed_at:
        sub.unsubscribed_at = datetime.utcnow()
        db.session.commit()
    return sub
