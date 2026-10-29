"""
Tâche Celery des relances de panier abandonné (services.cart_reminders)
"""
from celery_app import celery
from app import app


@celery.task(name='tasks.cart_reminder_tasks.send_cart_reminders')
def send_cart_reminders():
    from services import cart_reminders

    with app.app_context():
        return {'sent': cart_reminders.send_due()}
