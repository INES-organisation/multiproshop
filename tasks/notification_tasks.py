"""Vérification quotidienne des litiges CJ (notifications de l'admin)"""
from celery_app import celery
from app import app


@celery.task(name='tasks.notification_tasks.check_cj_disputes')
def check_cj_disputes():
    from config import Config
    from services import cj_disputes
    from services.api_providers.cj_dropshipping_optimized import CJDropshippingApiOptimized
    with app.app_context():
        api = CJDropshippingApiOptimized(email=Config.CJ_EMAIL, password=Config.CJ_PASSWORD, dev_key=Config.CJ_DEV_KEY)
        return {'notified': cj_disputes.check_new(api)}
