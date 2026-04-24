"""
Configuration Celery pour tâches asynchrones CJ Dropshipping
Gère les synchronisations en arrière-plan
"""
from celery import Celery
from celery.schedules import crontab
from config import Config
import os
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()

def make_celery(app_name=__name__):
    """Créer instance Celery"""
    
    # Configuration Redis
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    celery = Celery(
        app_name,
        broker=redis_url,
        backend=redis_url,
        include=[
            'tasks.cj_sync_tasks',
            'tasks.email_tasks',
            'tasks.analytics_tasks',
            'tasks.variant_sync_tasks'  # Nouvelles tâches de synchronisation variantes
        ]
    )
    
    # Configuration Celery
    celery.conf.update(
        # Timezone
        timezone='UTC',
        enable_utc=True,
        
        # Résultats
        result_expires=3600,  # 1 heure
        result_backend_transport_options={
            'master_name': 'mymaster'
        },
        
        # Tâches
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        
        # Performance
        worker_prefetch_multiplier=4,
        worker_max_tasks_per_child=1000,
        
        # Retry
        task_acks_late=True,
        task_reject_on_worker_lost=True,
        
        # Beat schedule (tâches périodiques)
        # CONFIGURATION DÉCALÉE - Évite conflits avec TonyAlpha80 (sync à 3h)
        # MultiProShop synchronise l'après-midi (15h-18h) = 12h d'écart
        beat_schedule={
            # ========================================
            # SYNCHRONISATIONS API CJ - APRÈS-MIDI (15h-18h)
            # Décalé de 12h par rapport à TonyAlpha80 (03h)
            # ========================================
            
            'sync-cj-products-daily': {
                'task': 'tasks.cj_sync_tasks.sync_products_task',
                'schedule': crontab(hour=15, minute=0),  # 15h00 (3h PM) - Décalé de TonyAlpha (03h00)
            },
            
            'sync-missing-variants-daily': {
                'task': 'tasks.variant_sync_tasks.sync_missing_variants',
                'schedule': crontab(hour=15, minute=30),  # 15h30 - Après sync produits
            },
            
            'update-stock-from-variants-daily': {
                'task': 'tasks.variant_sync_tasks.update_stock_from_variants',
                'schedule': crontab(hour=16, minute=0),  # 16h00 - Après sync variantes
            },
            
            'sync-cj-stock-hourly': {
                'task': 'tasks.cj_sync_tasks.sync_stock_task',
                'schedule': crontab(minute=30),  # XX:30 - Décalé de TonyAlpha (XX:00)
            },
            
            # ========================================
            # AUTRES TÂCHES (pas d'impact API CJ)
            # ========================================
            
            'sync-cj-orders-every-30min': {
                'task': 'tasks.cj_sync_tasks.sync_orders_task',
                'schedule': 1800.0,  # Toutes les 30 minutes (inchangé)
            },
            
            'cleanup-old-webhooks-weekly': {
                'task': 'tasks.analytics_tasks.cleanup_old_webhooks',
                'schedule': 604800.0,  # Toutes les semaines (inchangé)
            },
            
            'sync-reviews-weekly': {
                'task': 'sync_reviews_weekly',
                'schedule': crontab(hour=17, minute=0, day_of_week=0),  # Dimanche 17h
            },
            
            'cleanup-old-data-monthly': {
                'task': 'cleanup_old_data',
                'schedule': crontab(hour=18, minute=0, day_of_month=1),  # 1er du mois 18h
            },
        },
    )
    
    return celery

# Instance Celery globale
celery = make_celery()

if __name__ == '__main__':
    celery.start()
