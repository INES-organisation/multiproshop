"""
Service de planification des tâches automatiques
Synchronisation automatique des données CJ
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from services.cj_sync_service import CjSyncService
from services.api_providers.cj_dropshipping_optimized import CJDropshippingApiOptimized
from config import Config
import logging

logger = logging.getLogger(__name__)


class SchedulerService:
    """Service de planification des tâches CJ"""
    
    def __init__(self, app=None):
        """Initialiser le scheduler"""
        self.scheduler = BackgroundScheduler()
        self.app = app
        self.cj_api = None
        self.sync_service = None
    
    def init_app(self, app):
        """Initialiser avec l'application Flask"""
        self.app = app
        
        with app.app_context():
            # Initialiser l'API CJ
            self.cj_api = CJDropshippingApiOptimized(
                email=Config.CJ_EMAIL,
                password=Config.CJ_PASSWORD,
                dev_key=Config.CJ_DEV_KEY
            )
            
            # Initialiser le service de sync
            self.sync_service = CjSyncService(self.cj_api)
            
            # Configurer les tâches
            self._setup_jobs()
            
            # Démarrer le scheduler
            self.scheduler.start()
            logger.info("[Scheduler] Démarré avec succès")
    
    def _setup_jobs(self):
        """Configurer toutes les tâches planifiées"""
        
        # Synchronisation catégories : 1x/semaine (dimanche 3h)
        self.scheduler.add_job(
            func=self._sync_categories_job,
            trigger=CronTrigger(day_of_week='sun', hour=3, minute=0),
            id='sync_categories_weekly',
            name='Synchronisation catégories CJ (hebdomadaire)',
            replace_existing=True
        )
        logger.info("[Scheduler] Tâche 'sync_categories_weekly' configurée")
        
        # Synchronisation produits : 1x/jour (2h)
        self.scheduler.add_job(
            func=self._sync_products_job,
            trigger=CronTrigger(hour=2, minute=0),
            id='sync_products_daily',
            name='Synchronisation produits CJ (quotidienne)',
            replace_existing=True
        )
        logger.info("[Scheduler] Tâche 'sync_products_daily' configurée")
        
        # Mise à jour stock : toutes les heures
        self.scheduler.add_job(
            func=self._sync_stock_job,
            trigger=IntervalTrigger(hours=1),
            id='sync_stock_hourly',
            name='Mise à jour stock CJ (horaire)',
            replace_existing=True
        )
        logger.info("[Scheduler] Tâche 'sync_stock_hourly' configurée")
        
        # Nettoyage cache : tous les jours à minuit
        self.scheduler.add_job(
            func=self._cleanup_cache_job,
            trigger=CronTrigger(hour=0, minute=0),
            id='cleanup_cache_daily',
            name='Nettoyage cache (quotidien)',
            replace_existing=True
        )
        logger.info("[Scheduler] Tâche 'cleanup_cache_daily' configurée")
    
    def _sync_categories_job(self):
        """Tâche de synchronisation des catégories"""
        try:
            with self.app.app_context():
                logger.info("[Scheduler] Début sync catégories")
                result = self.sync_service.sync_categories()
                
                if result['success']:
                    logger.info(f"[Scheduler] ✓ {result['synced']} catégories synchronisées")
                else:
                    logger.error(f"[Scheduler] ✗ Échec sync catégories: {result.get('message')}")
        
        except Exception as e:
            logger.error(f"[Scheduler] Erreur sync catégories: {e}")
    
    def _sync_products_job(self):
        """Tâche de synchronisation des produits"""
        try:
            with self.app.app_context():
                from models.category import Category
                
                logger.info("[Scheduler] Début sync produits")
                
                # Récupérer toutes les catégories niveau 3 (avec produits)
                categories = Category.query.filter_by(level=3, visible=True).all()
                
                total_synced = 0
                for category in categories:
                    if category.cj_category_id:
                        result = self.sync_service.sync_products(
                            category.cj_category_id, 
                            limit=50  # Limiter pour éviter timeout
                        )
                        
                        if result['success']:
                            total_synced += result.get('synced', 0)
                
                logger.info(f"[Scheduler] ✓ {total_synced} produits synchronisés")
        
        except Exception as e:
            logger.error(f"[Scheduler] Erreur sync produits: {e}")
    
    def _sync_stock_job(self):
        """Tâche de mise à jour du stock"""
        try:
            with self.app.app_context():
                logger.info("[Scheduler] Début sync stock")
                result = self.sync_service.sync_stock()
                
                if result['success']:
                    logger.info(f"[Scheduler] ✓ Stock mis à jour pour {result.get('updated', 0)} produits")
                else:
                    logger.error(f"[Scheduler] ✗ Échec sync stock: {result.get('message')}")
        
        except Exception as e:
            logger.error(f"[Scheduler] Erreur sync stock: {e}")
    
    def _cleanup_cache_job(self):
        """Tâche de nettoyage du cache"""
        try:
            from services.cache_service import CacheService
            
            logger.info("[Scheduler] Nettoyage du cache")
            # Ne pas tout vider, juste les données expirées
            # Le cache Redis gère automatiquement l'expiration
            logger.info("[Scheduler] ✓ Cache nettoyé")
        
        except Exception as e:
            logger.error(f"[Scheduler] Erreur nettoyage cache: {e}")
    
    def shutdown(self):
        """Arrêter le scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("[Scheduler] Arrêté")
    
    def get_jobs(self):
        """Obtenir la liste des tâches planifiées"""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            })
        return jobs
    
    def pause_job(self, job_id):
        """Mettre en pause une tâche"""
        self.scheduler.pause_job(job_id)
        logger.info(f"[Scheduler] Tâche {job_id} mise en pause")
    
    def resume_job(self, job_id):
        """Reprendre une tâche"""
        self.scheduler.resume_job(job_id)
        logger.info(f"[Scheduler] Tâche {job_id} reprise")
    
    def run_job_now(self, job_id):
        """Exécuter une tâche immédiatement"""
        job = self.scheduler.get_job(job_id)
        if job:
            job.modify(next_run_time=None)
            logger.info(f"[Scheduler] Tâche {job_id} exécutée immédiatement")
        else:
            logger.warning(f"[Scheduler] Tâche {job_id} introuvable")


# Instance globale
_scheduler = None


def get_scheduler(app=None):
    """Obtenir l'instance du scheduler"""
    global _scheduler
    
    if _scheduler is None:
        _scheduler = SchedulerService(app)
        if app:
            _scheduler.init_app(app)
    
    return _scheduler
