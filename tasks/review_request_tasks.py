"""
Tâche Celery des demandes d'avis après livraison (services.review_requests)
"""
from celery_app import celery
from app import app


@celery.task(name='tasks.review_request_tasks.send_review_requests')
def send_review_requests():
    from services import review_requests

    with app.app_context():
        return {'sent': review_requests.send_due()}
