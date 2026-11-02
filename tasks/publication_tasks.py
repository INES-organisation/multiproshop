"""Mise en ligne d'un produit CJ après rédaction de sa fiche en français par Claude (via INES)"""
from celery_app import celery
from app import app


@celery.task(name='tasks.publication_tasks.write_and_publish')
def write_and_publish(product_id):
    with app.app_context():
        from services.publication import write_and_publish as run
        return run(product_id)
