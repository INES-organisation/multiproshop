"""
Worker de synchronisation en arrière-plan
Lance la synchronisation automatique des produits CJ
Inspiré de TonyAlpha80/workers/sync_worker.php
"""
import sys
import os
import time
import logging
from datetime import datetime

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from extensions import db
from services.background_sync_service import BackgroundSyncService
from services.api_providers.cj_dropshipping_optimized import CJDropshippingApiOptimized
from config import Config

# Créer le dossier logs s'il n'existe pas
logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
os.makedirs(logs_dir, exist_ok=True)

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(logs_dir, 'sync_worker.log')),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class SyncWorker:
    """Worker de synchronisation automatique"""
    
    def __init__(self):
        self.app = create_app()
        self.running = False
        
    def start(self):
        """Démarrer le worker"""
        logger.info("=" * 80)
        logger.info("🚀 DÉMARRAGE DU WORKER DE SYNCHRONISATION")
        logger.info("=" * 80)
        
        self.running = True
        
        with self.app.app_context():
            # Initialiser les services
            cj_api = CJDropshippingApiOptimized(
                email=Config.CJ_EMAIL,
                password=Config.CJ_PASSWORD
            )
            sync_service = BackgroundSyncService(db, cj_api)
            
            logger.info("✓ Services initialisés")
            logger.info(f"✓ Rate limit: {sync_service.rate_limit_seconds}s entre chaque batch")
            
            # Afficher les stats initiales
            stats = sync_service.get_sync_stats()
            logger.info(f"\n📊 STATISTIQUES INITIALES:")
            logger.info(f"  • Total produits CJ: {stats.get('total_cj_products', 0)}")
            logger.info(f"  • Produits actifs: {stats.get('active_cj_products', 0)}")
            logger.info(f"  • Jamais synchronisés: {stats.get('never_synced', 0)}")
            logger.info(f"  • Synchronisés 24h: {stats.get('synced_last_24h', 0)}")
            logger.info(f"  • Stock bas: {stats.get('low_stock', 0)}")
            logger.info(f"  • Rupture stock: {stats.get('out_of_stock', 0)}")
            logger.info("")
            
            cycle = 0
            
            while self.running:
                try:
                    cycle += 1
                    logger.info(f"\n{'=' * 80}")
                    logger.info(f"🔄 CYCLE #{cycle} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    logger.info(f"{'=' * 80}")
                    
                    # Vérifier le rate limit
                    if not sync_service.can_make_request():
                        wait_time = sync_service.get_wait_time()
                        logger.info(f"⏳ Rate limit actif, attente de {wait_time}s...")
                        time.sleep(min(wait_time, 60))
                        continue
                    
                    # Synchroniser un batch de produits
                    logger.info("📦 Synchronisation d'un batch de 10 produits...")
                    result = sync_service.sync_batch(batch_size=10)
                    
                    if result['success']:
                        logger.info(f"✅ {result['message']}")
                        logger.info(f"   • Synchronisés: {result['synced']}")
                        logger.info(f"   • Échecs: {result['failed']}")
                        logger.info(f"   • Durée: {result['duration']}")
                        
                        if result.get('errors'):
                            logger.warning(f"   ⚠️ Erreurs: {len(result['errors'])}")
                            for error in result['errors'][:3]:
                                logger.warning(f"      - {error}")
                    else:
                        logger.error(f"❌ {result['message']}")
                    
                    # Afficher les stats après le batch
                    stats = sync_service.get_sync_stats()
                    logger.info(f"\n📊 STATISTIQUES:")
                    logger.info(f"  • Jamais synchronisés: {stats.get('never_synced', 0)}")
                    logger.info(f"  • Synchronisés 24h: {stats.get('synced_last_24h', 0)}")
                    logger.info(f"  • Stock bas: {stats.get('low_stock', 0)}")
                    logger.info(f"  • Rupture stock: {stats.get('out_of_stock', 0)}")
                    
                    # Pause entre les cycles (5 minutes)
                    logger.info(f"\n💤 Pause de 5 minutes avant le prochain cycle...")
                    time.sleep(300)
                    
                except KeyboardInterrupt:
                    logger.info("\n⚠️ Interruption par l'utilisateur")
                    self.stop()
                    break
                    
                except Exception as e:
                    logger.error(f"❌ Erreur dans le cycle: {e}", exc_info=True)
                    logger.info("⏳ Pause de 60s avant de réessayer...")
                    time.sleep(60)
    
    def stop(self):
        """Arrêter le worker"""
        logger.info("\n" + "=" * 80)
        logger.info("🛑 ARRÊT DU WORKER DE SYNCHRONISATION")
        logger.info("=" * 80)
        self.running = False


def main():
    """Point d'entrée principal"""
    worker = SyncWorker()
    
    try:
        worker.start()
    except KeyboardInterrupt:
        logger.info("\n⚠️ Interruption par l'utilisateur")
        worker.stop()
    except Exception as e:
        logger.error(f"❌ Erreur fatale: {e}", exc_info=True)
        worker.stop()
        sys.exit(1)


if __name__ == '__main__':
    main()
