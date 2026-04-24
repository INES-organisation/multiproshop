"""
Script de récupération des 983 produits CJ supprimés
Ce script va resynchroniser tous les produits depuis l'API CJ Dropshipping
"""
import sys
import os
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app
from extensions import db
from models.product import Product
from models.category import Category
from services.api_providers.cj_dropshipping_optimized import CJDropshippingApiOptimized
from services.cj_sync_service import CjSyncService
import logging
import time

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_cj_credentials():
    """Récupérer les identifiants CJ depuis les variables d'environnement"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    email = os.getenv('CJ_EMAIL')
    password = os.getenv('CJ_PASSWORD')
    dev_key = os.getenv('CJ_DEV_KEY')
    
    if not email or not password:
        raise ValueError("CJ_EMAIL et CJ_PASSWORD doivent être définis dans .env")
    
    return email, password, dev_key


def count_current_products():
    """Compter les produits actuels dans la base"""
    total = Product.query.count()
    cj_products = Product.query.filter(Product.cj_pid.isnot(None)).count()
    published = Product.query.filter(Product.published == True).count()
    
    logger.info(f"📊 État actuel de la base:")
    logger.info(f"  - Total produits: {total}")
    logger.info(f"  - Produits CJ: {cj_products}")
    logger.info(f"  - Produits publiés: {published}")
    
    return total, cj_products, published


def sync_categories_first(cj_sync):
    """Synchroniser d'abord les catégories pour avoir la structure complète"""
    logger.info("🔄 Synchronisation des catégories CJ...")
    
    result = cj_sync.sync_categories()
    
    if result['success']:
        logger.info(f"✅ {result['synced']}/{result['total']} catégories synchronisées")
    else:
        logger.error(f"❌ Erreur sync catégories: {result['message']}")
        
    return result['success']


def recover_all_products(cj_api, cj_sync, batch_size=50, delay_between_batches=5):
    """
    Récupérer tous les produits CJ par lots
    
    Args:
        cj_api: Instance de l'API CJ
        cj_sync: Instance du service de synchronisation
        batch_size: Nombre de produits par lot
        delay_between_batches: Délai en secondes entre chaque lot
    """
    logger.info(f"🚀 Début de la récupération des produits CJ")
    logger.info(f"  - Taille des lots: {batch_size}")
    logger.info(f"  - Délai entre lots: {delay_between_batches}s")
    
    total_synced = 0
    page = 1
    max_pages = 100  # Limite de sécurité
    
    while page <= max_pages:
        logger.info(f"\n📦 Traitement page {page}...")
        
        try:
            # Récupérer les produits de cette page
            result = cj_api.get_products(
                page=page,
                page_size=batch_size,
                filters={}  # Tous les produits
            )
            
            if not result or 'products' not in result:
                logger.warning(f"⚠️ Aucun résultat pour la page {page}")
                break
            
            products = result.get('products', [])
            
            if not products:
                logger.info(f"✅ Fin de la récupération - aucun produit sur la page {page}")
                break
            
            logger.info(f"  - {len(products)} produits récupérés")
            
            # Synchroniser chaque produit
            synced_in_batch = 0
            errors_in_batch = 0
            
            for idx, product_data in enumerate(products, 1):
                try:
                    pid = product_data.get('pid')
                    name = product_data.get('name', 'Sans nom')[:50]
                    
                    logger.info(f"    [{idx}/{len(products)}] Sync: {name} (PID: {pid})")
                    
                    # Synchroniser le produit
                    cj_sync._sync_product(product_data)
                    db.session.commit()
                    
                    synced_in_batch += 1
                    total_synced += 1
                    
                    # Petit délai entre chaque produit pour éviter le rate limiting
                    time.sleep(0.5)
                    
                except Exception as e:
                    db.session.rollback()
                    logger.error(f"    ❌ Erreur sync produit: {e}")
                    errors_in_batch += 1
            
            logger.info(f"  ✅ Lot terminé: {synced_in_batch} réussis, {errors_in_batch} erreurs")
            logger.info(f"  📊 Total synchronisé: {total_synced}")
            
            # Vérifier s'il y a d'autres pages
            total_pages = result.get('total_pages', 1)
            total_count = result.get('total', 0)
            
            logger.info(f"  📄 Page {page}/{total_pages} - Total produits disponibles: {total_count}")
            
            if page >= total_pages:
                logger.info(f"✅ Toutes les pages traitées")
                break
            
            # Délai avant le prochain lot
            if page < total_pages:
                logger.info(f"  ⏳ Pause de {delay_between_batches}s avant le prochain lot...")
                time.sleep(delay_between_batches)
            
            page += 1
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du traitement de la page {page}: {e}")
            logger.info(f"  ⏳ Pause de 10s avant de réessayer...")
            time.sleep(10)
            page += 1
    
    return total_synced


def main():
    """Fonction principale de récupération"""
    logger.info("=" * 80)
    logger.info("🔧 SCRIPT DE RÉCUPÉRATION DES 983 PRODUITS CJ")
    logger.info("=" * 80)
    
    # Créer le contexte Flask
    app = create_app()
    
    with app.app_context():
        try:
            # 1. État initial
            logger.info("\n📊 ÉTAT INITIAL")
            logger.info("-" * 80)
            initial_total, initial_cj, initial_published = count_current_products()
            
            # 2. Récupérer les identifiants CJ
            logger.info("\n🔑 AUTHENTIFICATION CJ")
            logger.info("-" * 80)
            email, password, dev_key = get_cj_credentials()
            logger.info(f"  - Email: {email}")
            logger.info(f"  - Dev Key: {'✓' if dev_key else '✗'}")
            
            # 3. Initialiser l'API CJ
            cj_api = CJDropshippingApiOptimized(
                email=email,
                password=password,
                dev_key=dev_key
            )
            
            # Tester la connexion
            token = cj_api.get_access_token()
            if not token:
                logger.error("❌ Impossible d'obtenir le token d'accès CJ")
                return
            
            logger.info("✅ Authentification CJ réussie")
            
            # 4. Initialiser le service de synchronisation
            cj_sync = CjSyncService(cj_api)
            
            # 5. Synchroniser les catégories d'abord
            logger.info("\n📁 SYNCHRONISATION DES CATÉGORIES")
            logger.info("-" * 80)
            if not sync_categories_first(cj_sync):
                logger.warning("⚠️ Erreur lors de la sync des catégories, mais on continue...")
            
            # 6. Récupérer tous les produits
            logger.info("\n🔄 RÉCUPÉRATION DES PRODUITS")
            logger.info("-" * 80)
            
            total_synced = recover_all_products(
                cj_api=cj_api,
                cj_sync=cj_sync,
                batch_size=50,  # 50 produits par lot
                delay_between_batches=3  # 3 secondes entre chaque lot
            )
            
            # 7. Mettre à jour les compteurs de catégories
            logger.info("\n📊 MISE À JOUR DES COMPTEURS")
            logger.info("-" * 80)
            cj_sync._update_category_counts()
            logger.info("✅ Compteurs de catégories mis à jour")
            
            # 8. Lancer l'enrichissement automatique via Celery
            logger.info("\n🚀 LANCEMENT ENRICHISSEMENT AUTOMATIQUE")
            logger.info("-" * 80)
            try:
                from tasks.cj_sync_tasks import enrich_all_products_task
                
                # Lancer la tâche Celery pour enrichir tous les produits
                task = enrich_all_products_task.apply_async(
                    kwargs={
                        'batch_size': 20,
                        'delay_between_products': 1  # 1s entre chaque produit (optimisé)
                    }
                )
                
                logger.info(f"✅ Tâche d'enrichissement lancée (ID: {task.id})")
                logger.info("💡 Les workers Celery vont enrichir automatiquement tous les produits")
                logger.info("   - Description complète")
                logger.info("   - Toutes les variantes (couleurs, tailles)")
                logger.info("   - Stock par variante")
                logger.info("   - Avis clients")
                logger.info("   - Méthodes de livraison")
            except Exception as e:
                logger.warning(f"⚠️ Impossible de lancer l'enrichissement automatique: {e}")
                logger.info("💡 Vous pouvez lancer manuellement l'enrichissement depuis le dashboard Celery")
            
            # 8. État final
            logger.info("\n📊 ÉTAT FINAL")
            logger.info("-" * 80)
            final_total, final_cj, final_published = count_current_products()
            
            # 9. Résumé
            logger.info("\n" + "=" * 80)
            logger.info("📈 RÉSUMÉ DE LA RÉCUPÉRATION")
            logger.info("=" * 80)
            logger.info(f"  Produits synchronisés: {total_synced}")
            logger.info(f"  Avant: {initial_total} produits ({initial_cj} CJ, {initial_published} publiés)")
            logger.info(f"  Après: {final_total} produits ({final_cj} CJ, {final_published} publiés)")
            logger.info(f"  Gain: +{final_total - initial_total} produits")
            logger.info("=" * 80)
            
            if final_cj >= 983:
                logger.info("🎉 SUCCÈS ! Les 983 produits ont été récupérés !")
            else:
                logger.warning(f"⚠️ Seulement {final_cj}/983 produits récupérés")
                logger.info("💡 Vous pouvez relancer le script pour récupérer les produits manquants")
            
        except Exception as e:
            logger.error(f"❌ Erreur fatale: {e}")
            import traceback
            traceback.print_exc()
            return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
