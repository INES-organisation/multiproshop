"""
Utilitaires pour l'envoi d'emails

Plus de SMTP propre à la boutique : l'envoi passe par le fournisseur e-mail d'INES
(POST /api/v1/emails/transactional, même circuit que Digita). Sans INES_API_KEY, l'e-mail est
seulement journalisé et l'appelant continue. MAIL_FROM (facultatif) : expéditeur, à déclarer chez
le fournisseur d'INES ; sinon l'adresse par défaut d'INES avec le nom « MultiProShop ».
"""
import logging
import os
import re
from html import escape
from threading import Thread

import requests
from flask import render_template

logger = logging.getLogger(__name__)

FROM_NAME = 'MultiProShop'


# ---------------------------------------------------------------- mise en page commune (04/11/2026)
# Tous les e-mails passent par layout() : logo, couleurs de la boutique, pied de page légal. Tableaux
# et styles en ligne : seule forme rendue pareil dans Gmail, Outlook et Apple Mail. Les modèles
# templates/emails/*.html ne contiennent plus que le corps du message.
ORANGE, INK, MUTED, LINE, BG = '#f59e0b', '#1f2937', '#4b5563', '#ece7dc', '#faf8f4'


def _cfg():
    from config import Config
    return Config.SITE_URL.rstrip('/'), Config.SELLER


def layout(title, content_html, preheader=''):
    site, seller = _cfg()
    return f"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)}</title></head>
<body style="margin:0;padding:0;background:{BG};font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;">
<div style="display:none;max-height:0;overflow:hidden;">{escape(preheader)}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{BG};padding:32px 16px;"><tr><td align="center">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;background:#ffffff;border-radius:14px;overflow:hidden;border:1px solid {LINE};">
<tr><td align="center" style="padding:24px 32px 18px;border-bottom:4px solid {ORANGE};">
<a href="{site}"><img src="{site}/static/images/email/logo-email.png" width="150" alt="MultiProShop" style="display:block;border:0;width:150px;height:auto;"></a>
</td></tr>
<tr><td style="padding:32px 32px 12px;font-size:15px;line-height:1.7;color:{MUTED};">
<h1 style="margin:0 0 18px;font-size:22px;line-height:1.35;font-weight:700;color:{INK};">{escape(title)}</h1>
{content_html}
</td></tr>
<tr><td style="padding:20px 32px;background:{BG};border-top:1px solid {LINE};font-size:12px;line-height:1.7;color:{MUTED};">
<strong style="color:{INK};">{escape(seller['trade_name'])}</strong> · {escape(seller['company'])} · {escape(seller['legal_form'])} · SIREN {escape(seller['siren'])}<br>
{escape(seller['address'])}, {escape(seller['postal_code'])} {escape(seller['city'])} · {escape(seller['phone'])} ·
<a href="mailto:{escape(seller['email'])}" style="color:{MUTED};">{escape(seller['email'])}</a><br>
<a href="{site}/suivi-commande" style="color:{INK};">Suivre une commande</a> ·
<a href="{site}/legal" style="color:{MUTED};">Mentions légales</a>
</td></tr>
</table>
<p style="margin:16px 0 0;font-size:11px;color:#9ca3af;">E-mail automatique envoyé par multiproshop.com.</p>
</td></tr></table>
</body></html>"""


_BODY = re.compile(r'<body[^>]*>(.*)</body>', re.S | re.I)
_STYLE = re.compile(r'<style.*?</style>', re.S | re.I)
_TITLE_TAG = re.compile(r'^\s*<h[12][^>]*>.*?</h[12]>', re.S | re.I)


def wrap(subject, html):
    """Met n'importe quel corps (fragment ou ancien document complet) dans la mise en page commune."""
    if 'data-mps-email' in html:
        return html
    m = _BODY.search(html)
    inner = _STYLE.sub('', m.group(1) if m else html)
    inner = _TITLE_TAG.sub('', inner, count=1)  # le titre est repris en tête par layout()
    title = re.sub(r'^\[MultiProShop\]\s*|\s*[-—]\s*MultiProShop\s*$', '', subject or '').strip() or 'MultiProShop'
    return layout(title, inner).replace('<body ', '<body data-mps-email="1" ', 1)


def _send_via_ines(to, subject, html, template=None):
    if not os.getenv('INES_API_KEY'):
        logger.warning("INES non configuré, e-mail non envoyé : %s → %s", subject, to)
        return False
    html = wrap(subject, html)
    url = os.getenv('INES_API_URL', 'http://ines-backend:8000').rstrip('/') + '/api/v1/emails/transactional'
    # site/template : libellé dans le journal d'INES (Communications › Journal).
    body = {'to': to, 'subject': subject, 'html': html, 'from_name': FROM_NAME,
            'from_address': os.getenv('MAIL_FROM') or None, 'site': 'multiproshop', 'template': template}
    try:
        requests.post(url, json=body, headers={'Authorization': 'Bearer ' + os.getenv('INES_API_KEY', '')},
                      timeout=30).raise_for_status()
        return True
    except requests.RequestException as e:
        logger.error("E-mail non envoyé par INES à %s (%s) : %s", to, subject, e)
        return False


def send_email(subject=None, recipients=None, text_body=None, html_body=None, to=None, html=None, text=None,
               template=None):
    """
    Envoyer un email (en arrière-plan), toujours dans la mise en page commune.

    Deux formes acceptées, toutes deux utilisées dans le code :
        send_email(subject, recipients, text_body, html_body)
        send_email(to=..., subject=..., html=..., text=...)
    """
    if to:
        recipients = [to] if isinstance(to, str) else list(to)
    html_body = html_body or html or ('<p style="white-space:pre-line;">%s</p>' % escape(text_body or text or ''))
    for recipient in recipients or []:
        Thread(target=_send_via_ines, args=(recipient, subject, html_body, template), daemon=True).start()


def send_order_confirmation_email(order):
    """
    Envoyer un email de confirmation de commande
    
    Args:
        order: Instance du modèle Order
    """
    subject = f"Confirmation de commande {order.order_number} - MultiProShop"
    recipients = [order.customer_email]
    
    # Rendu du template HTML
    html_body = render_template('emails/order_confirmation.html', order=order)
    
    # Version texte brut
    text_body = f"""
Bonjour {order.shipping_first_name},

Merci pour votre commande !

Numéro de commande : {order.order_number}
Date : {order.created_at.strftime('%d/%m/%Y à %H:%M')}
Montant total : {order.total_price:.2f}€

Votre commande est en cours de traitement. Vous recevrez un email de confirmation dès son expédition.

Cordialement,
L'équipe MultiProShop
"""
    
    send_email(subject, recipients, text_body, html_body, template='commande')

def send_order_shipped_email(order, tracking_number=None):
    """
    Envoyer un email d'expédition de commande
    
    Args:
        order: Instance du modèle Order
        tracking_number: Numéro de suivi (optionnel)
    """
    subject = f"Votre commande {order.order_number} a été expédiée - MultiProShop"
    recipients = [order.customer_email]
    
    # Rendu du template HTML
    html_body = render_template('emails/order_shipped.html', order=order, tracking_number=tracking_number)
    
    # Version texte brut
    text_body = f"""
Bonjour {order.shipping_first_name},

Bonne nouvelle ! Votre commande {order.order_number} a été expédiée.

"""
    
    if tracking_number:
        text_body += f"Numéro de suivi : {tracking_number}\n\n"
    
    text_body += f"""
Adresse de livraison :
{order.shipping_address}
{order.shipping_postal_code} {order.shipping_city}
{order.shipping_country}

Vous recevrez votre colis sous 2-5 jours ouvrés.

Cordialement,
L'équipe MultiProShop
"""
    
    send_email(subject, recipients, text_body, html_body, template='expedition')

def send_order_delivered_email(order):
    """
    Envoyer un email de livraison de commande
    
    Args:
        order: Instance du modèle Order
    """
    subject = f"Votre commande {order.order_number} a été livrée - MultiProShop"
    recipients = [order.customer_email]
    
    # Rendu du template HTML
    html_body = render_template('emails/order_delivered.html', order=order)
    
    # Version texte brut
    text_body = f"""
Bonjour {order.shipping_first_name},

Votre commande {order.order_number} a été livrée avec succès !

Nous espérons que vous êtes satisfait(e) de votre achat.

N'hésitez pas à nous laisser un avis sur nos produits.

Cordialement,
L'équipe MultiProShop
"""
    
    send_email(subject, recipients, text_body, html_body, template='livraison')
