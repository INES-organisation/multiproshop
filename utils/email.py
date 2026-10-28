"""
Utilitaires pour l'envoi d'emails

Plus de SMTP propre à la boutique : l'envoi passe par le fournisseur e-mail d'INES
(POST /api/v1/emails/transactional, même circuit que Digita). Sans INES_API_KEY, l'e-mail est
seulement journalisé et l'appelant continue. MAIL_FROM (facultatif) : expéditeur, à déclarer chez
le fournisseur d'INES ; sinon l'adresse par défaut d'INES avec le nom « MultiProShop ».
"""
import logging
import os
from html import escape
from threading import Thread

import requests
from flask import render_template

logger = logging.getLogger(__name__)

FROM_NAME = 'MultiProShop'


def _send_via_ines(to, subject, html):
    if not os.getenv('INES_API_KEY'):
        logger.warning("INES non configuré, e-mail non envoyé : %s → %s", subject, to)
        return False
    url = os.getenv('INES_API_URL', 'http://ines-backend:8000').rstrip('/') + '/api/v1/emails/transactional'
    body = {'to': to, 'subject': subject, 'html': html, 'from_name': FROM_NAME,
            'from_address': os.getenv('MAIL_FROM') or None}
    try:
        requests.post(url, json=body, headers={'Authorization': 'Bearer ' + os.getenv('INES_API_KEY', '')},
                      timeout=30).raise_for_status()
        return True
    except requests.RequestException as e:
        logger.error("E-mail non envoyé par INES à %s (%s) : %s", to, subject, e)
        return False


def send_email(subject=None, recipients=None, text_body=None, html_body=None, to=None, html=None, text=None):
    """
    Envoyer un email (en arrière-plan)

    Deux formes acceptées, toutes deux utilisées dans le code :
        send_email(subject, recipients, text_body, html_body)
        send_email(to=..., subject=..., html=..., text=...)
    """
    if to:
        recipients = [to] if isinstance(to, str) else list(to)
    html_body = html_body or html or ('<pre>%s</pre>' % escape(text_body or text or ''))
    for recipient in recipients or []:
        Thread(target=_send_via_ines, args=(recipient, subject, html_body), daemon=True).start()

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
    
    send_email(subject, recipients, text_body, html_body)

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
    
    send_email(subject, recipients, text_body, html_body)

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
    
    send_email(subject, recipients, text_body, html_body)
