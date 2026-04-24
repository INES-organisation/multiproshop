"""
Script pour récupérer TOUS les produits CJ disponibles
Récupère par catégorie pour avoir tous les produits (des dizaines de milliers)
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app
from extensions import db
from models.product import Product
from models.category import Category
from services.api_providers.cj_dropshipping_optimized import CJDropshippingApiOptimized
from services.cj_sync_service import CjSyncService
from config import Config
import logging
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

stats = {
    'synced': 0,
    'errors': 0,
    'categories_processed': 0
}


def main():
    """Fonction principale"""
    logger.info("=" * 80)
    logger.info("🚀 RÉCUPÉRATION DE TOUS LES PRODUITS CJ")
    logger.info("=" * 80)
    
    app = create_app()
    
    with app.app_context():
        try:
            # 1. État initial
            logger.info("\n📊 ÉTAT INITIAL")
            logger.info("-" * 80)
            initial_count = Product.query.filter(Product.cj_pid.isnot(None)).count()
            logger.info(f"  Produits CJ actuels: {initial_count}")
            
            # 2. Initialiser l'API
            logger.info("\n🔑 CONNEXION API CJ")
            logger.info("-" * 80)
            cj_api = CJDropshippingApiOptimized(
                email=Config.CJ_EMAIL,
                password=Config.CJ_PASSWORD,
                dev_key=Config.CJ_DEV_KEY
            )
            cj_sync = CjSyncService(cj_api)
            logger.info("✅ Connexion établie")
            
            # 3. Synchroniser les catégories d'abord
            logger.info("\n📁 SYNCHRONISATION DES CATÉGORIES")
            logger.info("-" * 80)
            cat_result = cj_sync.sync_categories()
            logger.info(f"✅ {cat_result.get('synced', 0)} catégories synchronisées")
            
            # 4. Récupérer toutes les catégories CJ niveau 3 (les plus spécifiques)
            logger.info("\n🔍 RÉCUPÉRATION DES CATÉGORIES")
            logger.info("-" * 80)
            
            # Récupérer toutes les catégories CJ (tous niveaux)
            all_categories = Category.query.filter(
                Category.cj_category_id.isnot(None)
            ).order_by(Category.level.desc()).all()
            
            total_categories = len(all_categories)
            logger.info(f"✅ {total_categories} catégories CJ trouvées")
            
            # 5. Synchroniser les produits par catégorie
            logger.info("\n📦 SYNCHRONISATION DES PRODUITS PAR CATÉGORIE")
            logger.info("-" * 80)
            logger.info(f"  Mode: Par catégorie (pour avoir TOUS les produits)")
            logger.info(f"  Limite par catégorie: 1000 produits")
            logger.info(f"  Délai entre catégories: 2 secondes")
            
            start_time = time.time()
            
            for idx, category in enumerate(all_categories, 1):
                try:
                    logger.info(f"\n📂 [{idx}/{total_categories}] Catégorie: {category.name}")
                    
                    # Synchroniser les produits de cette catégorie
                    result = cj_sync.sync_products(
                        category_id=category.cj_category_id,
                        limit=1000  # Maximum par catégorie
                    )
                    
                    if result.get('success'):
                        synced = result.get('synced', 0)
                        stats['synced'] += synced
                        stats['categories_processed'] += 1
                        
                        logger.info(f"  ✅ {synced} produits synchronisés")
                    else:
                        logger.warning(f"  ⚠️ Erreur: {result.get('message', 'Inconnue')}")
                        stats['errors'] += 1
                    
                    # Afficher progression tous les 10 catégories
                    if idx % 10 == 0:
                        elapsed = time.time() - start_time
                        rate = idx / elapsed if elapsed > 0 else 0
                        remaining = total_categories - idx
                        eta_seconds = remaining / rate if rate > 0 else 0
                        eta_minutes = int(eta_seconds / 60)
                        
                        current_count = Product.query.filter(Product.cj_pid.isnot(None)).count()
                        new_products = current_count - initial_count
                        
                        logger.info(f"\n📊 PROGRESSION:")
                        logger.info(f"  Catégories: {idx}/{total_categories}")
                        logger.info(f"  Produits synchronisés: {stats['synced']}")
                        logger.info(f"  Nouveaux produits: {new_products}")
                        logger.info(f"  ETA: ~{eta_minutes}min")
                    
                    # Délai entre catégories
                    time.sleep(2)
                    
                except Exception as e:
                    logger.error(f"  ❌ Erreur catégorie {category.name}: {e}")
                    stats['errors'] += 1
                    time.sleep(3)
            
            # 6. Mettre à jour les compteurs
            logger.info("\n📊 MISE À JOUR DES COMPTEURS")
            logger.info("-" * 80)
            cj_sync._update_category_counts()
            logger.info("✅ Compteurs mis à jour")
            
            # 7. État final
            logger.info("\n📊 ÉTAT FINAL")
            logger.info("-" * 80)
            final_count = Product.query.filter(Product.cj_pid.isnot(None)).count()
            new_products = final_count - initial_count
            
            elapsed_total = time.time() - start_time
            
            logger.info("\n" + "=" * 80)
            logger.info("✅ SYNCHRONISATION TERMINÉE")
            logger.info("=" * 80)
            logger.info(f"  Catégories traitées: {stats['categories_processed']}/{total_categories}")
            logger.info(f"  Produits avant: {initial_count}")
            logger.info(f"  Produits après: {final_count}")
            logger.info(f"  Nouveaux produits: {new_products}")
            logger.info(f"  Erreurs: {stats['errors']}")
            logger.info(f"  Temps total: {int(elapsed_total / 60)}min {int(elapsed_total % 60)}s")
            logger.info("=" * 80)
            
            logger.info("\n💡 PROCHAINES ÉTAPES:")
            logger.info("  1. Vider le cache: python scripts\\clear_cache_and_enrich.py")
            logger.info("  2. Enrichir les produits: python scripts\\enrich_all_products_now.py")
            
            return 0
            
        except Exception as e:
            logger.error(f"❌ Erreur fatale: {e}")
            import traceback
            traceback.print_exc()
            return 1


if __name__ == '__main__':
    exit(main())
