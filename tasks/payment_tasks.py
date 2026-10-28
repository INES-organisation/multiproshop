"""
Tâches Celery du paiement : rattrapage des commandes payées dont le client n'est pas revenu
sur le site (onglet fermé avant la redirection).
"""
from celery_app import celery
from app import app
import logging

logger = logging.getLogger(__name__)


@celery.task(name='tasks.payment_tasks.reconcile_pending_orders')
def reconcile_pending_orders():
    from services import ines_payment

    with app.app_context():
        if not ines_payment.enabled():
            return {'skipped': 'INES_API_KEY absente'}
        stats = ines_payment.reconcile_pending_orders()
        if stats['paid'] or stats['cancelled']:
            logger.info(f"[Celery] Paiements rattrapés : {stats}")
        return stats
