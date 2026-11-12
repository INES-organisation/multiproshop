"""Recherche de produits (admin MPS › Recherche de produits) : un passage de veille, et le passage du lundi"""
from celery_app import celery
from app import app


@celery.task(name='tasks.research_tasks.run_watch', time_limit=3 * 3600)
def run_watch(watch_id):
    with app.app_context():
        from extensions import db
        from models.product_research import ResearchWatch
        from services.product_research import run_watch as run
        watch = db.session.get(ResearchWatch, watch_id)
        return run(watch) if watch else None


@celery.task(name='tasks.research_tasks.run_active_watches', time_limit=6 * 3600)
def run_active_watches():
    with app.app_context():
        from services.product_research import run_active
        return run_active()
