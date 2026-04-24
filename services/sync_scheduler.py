"""
Système de synchronisation automatique pour les providers
Utilise APScheduler pour les tâches planifiées
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
from typing import Optional
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SyncScheduler:
    """Gestionnaire de synchronisations planifiées"""
    
    def __init__(self, app=None):
        """
        Initialiser le scheduler
        
        Args:
            app: Instance Flask (optionnel)
        """
        self.scheduler = BackgroundScheduler()
        self.app = app
        self.jobs = {}
    
    def init_app(self, app):
        """Initialiser avec l'application Flask"""
        self.app = app
        
        # Démarrer le scheduler
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("✅ Scheduler de synchronisation démarré")
    
    def add_sync_job(self, provider_id: int, schedule_type: str = 'daily', 
                     hour: int = 2, minute: int = 0, interval_hours: Optional[int] = None):
        """
        Ajouter une tâche de synchronisation
        
        Args:
            provider_id: ID du provider
            schedule_type: 'daily', 'hourly', 'interval', 'weekly'
            hour: Heure d'exécution (pour daily/weekly)
            minute: Minute d'exécution
            interval_hours: Intervalle en heures (pour interval)
        """
        job_id = f'sync_provider_{provider_id}'
        
        # Supprimer l'ancien job s'il existe
        if job_id in self.jobs:
            self.remove_sync_job(provider_id)
        
        # Créer le trigger selon le type
        if schedule_type == 'daily':
            trigger = CronTrigger(hour=hour, minute=minute)
        elif schedule_type == 'hourly':
            trigger = CronTrigger(minute=minute)
        elif schedule_type == 'weekly':
            trigger = CronTrigger(day_of_week='mon', hour=hour, minute=minute)
        elif schedule_type == 'interval' and interval_hours:
            trigger = IntervalTrigger(hours=interval_hours)
        else:
            logger.error(f"Type de schedule invalide: {schedule_type}")
            return False
        
        # Ajouter le job
        job = self.scheduler.add_job(
            func=self._sync_provider_task,
            trigger=trigger,
            args=[provider_id],
            id=job_id,
            name=f'Sync Provider {provider_id}',
            replace_existing=True
        )
        
        self.jobs[job_id] = job
        logger.info(f"✅ Job de sync ajouté pour provider {provider_id}: {schedule_type}")
        
        return True
    
    def remove_sync_job(self, provider_id: int):
        """Supprimer une tâche de synchronisation"""
        job_id = f'sync_provider_{provider_id}'
        
        if job_id in self.jobs:
            self.scheduler.remove_job(job_id)
            del self.jobs[job_id]
            logger.info(f"🗑️  Job de sync supprimé pour provider {provider_id}")
            return True
        
        return False
    
    def _sync_provider_task(self, provider_id: int):
        """
        Tâche de synchronisation d'un provider
        Exécutée par le scheduler
        """
        if not self.app:
            logger.error("Application Flask non initialisée")
            return
        
        with self.app.app_context():
            try:
                from models.api_provider import ApiProvider, ProductSource, ApiSyncLog
                from routes.api_management import get_provider_service
                from extensions import db
                
                logger.info(f"🔄 Début sync provider {provider_id}")
                
                # Récupérer le provider
                provider = ApiProvider.query.get(provider_id)
                if not provider or not provider.is_active:
                    logger.warning(f"Provider {provider_id} inactif ou introuvable")
                    return
                
                # Créer un log de sync
                sync_log = ApiSyncLog(
                    provider_id=provider_id,
                    sync_type='scheduled_sync',
                    status='running',
                    started_at=datetime.utcnow()
                )
                db.session.add(sync_log)
                db.session.commit()
                
                # Obtenir le service
                service = get_provider_service(provider)
                
                # Synchroniser les stocks des produits existants
                sources = ProductSource.query.filter_by(
                    provider_id=provider_id,
                    is_active=True
                ).all()
                
                synced = 0
                failed = 0
                
                for source in sources:
                    try:
                        success = service.sync_product_stock(source)
                        if success:
                            synced += 1
                        else:
                            failed += 1
                    except Exception as e:
                        logger.error(f"Erreur sync produit {source.id}: {e}")
                        failed += 1
                
                # Mettre à jour le log
                sync_log.status = 'success'
                sync_log.items_processed = len(sources)
                sync_log.items_updated = synced
                sync_log.items_failed = failed
                sync_log.completed_at = datetime.utcnow()
                sync_log.duration_seconds = int((sync_log.completed_at - sync_log.started_at).total_seconds())
                sync_log.message = f'{synced} produits synchronisés, {failed} échecs'
                
                provider.last_sync_at = datetime.utcnow()
                
                db.session.commit()
                
                logger.info(f"✅ Sync terminée pour provider {provider_id}: {synced} OK, {failed} KO")
                
            except Exception as e:
                logger.error(f"❌ Erreur sync provider {provider_id}: {e}")
                
                # Mettre à jour le log en erreur
                if 'sync_log' in locals():
                    sync_log.status = 'error'
                    sync_log.error_details = str(e)
                    sync_log.completed_at = datetime.utcnow()
                    db.session.commit()
    
    def sync_all_active_providers(self):
        """Synchroniser tous les providers actifs manuellement"""
        if not self.app:
            logger.error("Application Flask non initialisée")
            return
        
        with self.app.app_context():
            from models.api_provider import ApiProvider
            
            providers = ApiProvider.query.filter_by(is_active=True).all()
            
            for provider in providers:
                self._sync_provider_task(provider.id)
    
    def get_jobs_status(self):
        """Obtenir le statut de tous les jobs"""
        jobs_info = []
        
        for job in self.scheduler.get_jobs():
            jobs_info.append({
                'id': job.id,
                'name': job.name,
                'next_run': job.next_run_time,
                'trigger': str(job.trigger)
            })
        
        return jobs_info
    
    def shutdown(self):
        """Arrêter le scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("🛑 Scheduler arrêté")


# Instance globale
_scheduler = None

def get_scheduler(app=None) -> SyncScheduler:
    """Obtenir l'instance du scheduler"""
    global _scheduler
    
    if _scheduler is None:
        _scheduler = SyncScheduler(app)
    elif app and not _scheduler.app:
        _scheduler.init_app(app)
    
    return _scheduler
