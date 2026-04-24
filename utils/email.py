"""
Utilitaires pour l'envoi d'emails
"""
from flask import render_template, current_app
from flask_mail import Message
from extensions import mail
from threading import Thread

def send_async_email(app, msg):
    """Envoyer un email de manière asynchrone"""
    with app.app_context():
        mail.send(msg)

def send_email(subject, recipients, text_body=None, html_body=None):
    """
    Envoyer un email
    
    Args:
        subject: Sujet de l'email
        recipients: Liste des destinataires
        text_body: Corps du message en texte brut
        html_body: Corps du message en HTML
    """
    msg = Message(subject, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    
    # Envoyer de manière asynchrone
    Thread(target=send_async_email, args=(current_app._get_current_object(), msg)).start()

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
