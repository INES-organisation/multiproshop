"""
Tâches Celery pour analytics et maintenance
"""
from celery_app import celery
from app import app
from models.webhook_log import WebhookLog
from extensions import db
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@celery.task(name='tasks.analytics_tasks.cleanup_old_webhooks')
def cleanup_old_webhooks():
    """
    Tâche asynchrone: Nettoyer les anciens logs webhooks (> 90 jours)
    """
    try:
        with app.app_context():
            logger.info("[Celery] Nettoyage anciens webhooks")
            
            # Supprimer logs > 90 jours
            ninety_days_ago = datetime.now() - timedelta(days=90)
            
            deleted = WebhookLog.query.filter(
                WebhookLog.created_at < ninety_days_ago
            ).delete()
            
            db.session.commit()
            
            logger.info(f"[Celery] ✅ {deleted} anciens webhooks supprimés")
            
            return {
                'status': 'success',
                'deleted': deleted
            }
            
    except Exception as e:
        logger.error(f"[Celery] Erreur cleanup webhooks: {e}")
        db.session.rollback()
        return {
            'status': 'error',
            'message': str(e)
        }
