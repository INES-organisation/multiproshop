"""
Tâches Celery pour envoi d'emails asynchrones
"""
from celery_app import celery
from app import app
from utils.email import send_email
import logging

logger = logging.getLogger(__name__)


@celery.task(name='tasks.email_tasks.send_email_async', bind=True, max_retries=3)
def send_email_async(self, to, subject, html, text=None):
    """
    Tâche asynchrone: Envoyer un email
    
    Args:
        to: Email destinataire
        subject: Sujet
        html: Contenu HTML
        text: Contenu texte (optionnel)
    """
    try:
        with app.app_context():
            logger.info(f"[Celery] Envoi email à {to}")
            
            send_email(
                to=to,
                subject=subject,
                html=html,
                text=text
            )
            
            logger.info(f"[Celery] ✅ Email envoyé à {to}")
            
            return {
                'status': 'success',
                'to': to
            }
            
    except Exception as e:
        logger.error(f"[Celery] Erreur envoi email: {e}")
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


@celery.task(name='tasks.email_tasks.send_bulk_emails', bind=True)
def send_bulk_emails_task(self, recipients, subject, html, text=None):
    """
    Tâche asynchrone: Envoyer des emails en masse
    
    Args:
        recipients: Liste d'emails
        subject: Sujet
        html: Contenu HTML
        text: Contenu texte (optionnel)
    """
    try:
        with app.app_context():
            logger.info(f"[Celery] Envoi bulk emails à {len(recipients)} destinataires")
            
            sent = 0
            errors = []
            
            for recipient in recipients:
                try:
                    send_email(
                        to=recipient,
                        subject=subject,
                        html=html,
                        text=text
                    )
                    sent += 1
                except Exception as e:
                    logger.error(f"[Celery] Erreur envoi à {recipient}: {e}")
                    errors.append({'recipient': recipient, 'error': str(e)})
            
            logger.info(f"[Celery] ✅ Bulk emails: {sent}/{len(recipients)} envoyés")
            
            return {
                'status': 'success',
                'sent': sent,
                'total': len(recipients),
                'errors': errors
            }
            
    except Exception as e:
        logger.error(f"[Celery] Erreur bulk emails: {e}")
        return {
            'status': 'error',
            'message': str(e)
        }
