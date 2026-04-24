"""
Script de récupération RAPIDE des produits CJ manquants
Optimisé pour aller le plus vite possible sans dépasser les limites API
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
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Compteurs thread-safe
lock = threading.Lock()
stats = {
    'synced': 0,
    'errors': 0,
    'skipped': 0
}


def get_cj_credentials():
    """Récupérer les identifiants CJ"""
    from dotenv import load_dotenv
    load_dotenv()
    
    email = os.getenv('CJ_EMAIL')
    password = os.getenv('CJ_PASSWORD')
    dev_key = os.getenv('CJ_DEV_KEY')
    
    if not email or not password:
        raise ValueError("CJ_EMAIL et CJ_PASSWORD doivent être définis dans .env")
    
    return email, password, dev_key


def count_current_products():
    """Compter les produits actuels"""
    total = Product.query.count()
    cj_products = Product.query.filter(Product.cj_pid.isnot(None)).count()
    published = Product.query.filter(
        Product.cj_pid.isnot(None),
        Product.published == True
    ).count()
    return total, cj_products, published


def sync_product_batch(cj_api, cj_sync, products_data, batch_num):
    """Synchroniser un lot de produits"""
    app = create_app()
    
    with app.app_context():
        for idx, product_data in enumerate(products_data):
            try:
                cj_sync._sync_product(product_data)
                
                with lock:
                    stats['synced'] += 1
                    
                if (stats['synced'] + stats['errors']) % 50 == 0:
                    logger.info(f"📊 Progression: {stats['synced']} synced, {stats['errors']} errors")
                    
            except Exception as e:
                with lock:
                    stats['errors'] += 1
                logger.error(f"❌ Erreur produit {product_data.get('pid', 'N/A')}: {e}")
        
        db.session.commit()


def main():
    """Fonction principale optimisée"""
    logger.info("=" * 80)
    logger.info("🚀 RÉCUPÉRATION RAPIDE DES PRODUITS CJ")
    logger.info("=" * 80)
    
    app = create_app()
    
    with app.app_context():
        try:
            # 1. État initial
            logger.info("\n📊 ÉTAT INITIAL")
            logger.info("-" * 80)
            total_before, cj_before, published_before = count_current_products()
            logger.info(f"  Produits totaux: {total_before}")
            logger.info(f"  Produits CJ: {cj_before}")
            logger.info(f"  Produits publiés: {published_before}")
            
            # 2. Initialiser l'API CJ
            logger.info("\n🔑 CONNEXION À L'API CJ")
            logger.info("-" * 80)
            email, password, dev_key = get_cj_credentials()
            cj_api = CJDropshippingApiOptimized(email, password, dev_key)
            cj_sync = CjSyncService(cj_api)
            logger.info("✅ Connexion établie")
            
            # 3. Synchroniser les catégories
            logger.info("\n📁 SYNCHRONISATION DES CATÉGORIES")
            logger.info("-" * 80)
            cat_result = cj_sync.sync_categories()
            logger.info(f"✅ {cat_result.get('synced', 0)} catégories synchronisées")
            
            # 4. Récupérer TOUS les produits de l'API
            logger.info("\n📦 RÉCUPÉRATION DES PRODUITS")
            logger.info("-" * 80)
            logger.info("⏳ Récupération de la liste complète depuis l'API...")
            
            all_products = []
            page = 1
            page_size = 100  # Maximum par page
            
            while True:
                logger.info(f"  Page {page}...")
                
                products_data = cj_api.get_products(
                    page=page,
                    page_size=page_size
                )
                
                if not products_data or not products_data.get('data'):
                    break
                
                products = products_data['data'].get('list', [])
                if not products:
                    break
                
                all_products.extend(products)
                logger.info(f"  ✅ {len(products)} produits récupérés (Total: {len(all_products)})")
                
                # Vérifier s'il y a d'autres pages
                total_available = products_data['data'].get('total', 0)
                if len(all_products) >= total_available:
                    break
                
                page += 1
                time.sleep(0.5)  # Petit délai entre les pages
            
            logger.info(f"\n✅ {len(all_products)} produits récupérés de l'API")
            
            # 5. Filtrer les produits déjà en base
            logger.info("\n🔍 FILTRAGE DES PRODUITS")
            logger.info("-" * 80)
            
            existing_pids = set(
                p[0] for p in db.session.query(Product.cj_pid).filter(
                    Product.cj_pid.isnot(None)
                ).all()
            )
            
            products_to_sync = [
                p for p in all_products 
                if p.get('pid') not in existing_pids
            ]
            
            logger.info(f"  Produits en base: {len(existing_pids)}")
            logger.info(f"  Produits à synchroniser: {len(products_to_sync)}")
            
            if len(products_to_sync) == 0:
                logger.info("\n✅ Tous les produits sont déjà synchronisés !")
                return 0
            
            # 6. Synchronisation RAPIDE par lots
            logger.info("\n⚡ SYNCHRONISATION RAPIDE")
            logger.info("-" * 80)
            logger.info(f"  Mode: Lots de 50 produits")
            logger.info(f"  Délai entre lots: 2 secondes")
            
            batch_size = 50
            total_batches = (len(products_to_sync) + batch_size - 1) // batch_size
            
            for batch_num in range(total_batches):
                start_idx = batch_num * batch_size
                end_idx = min(start_idx + batch_size, len(products_to_sync))
                batch = products_to_sync[start_idx:end_idx]
                
                logger.info(f"\n📦 Lot {batch_num + 1}/{total_batches} ({len(batch)} produits)")
                
                # Synchroniser le lot
                for product_data in batch:
                    try:
                        cj_sync._sync_product(product_data)
                        stats['synced'] += 1
                    except Exception as e:
                        stats['errors'] += 1
                        logger.error(f"❌ Erreur: {e}")
                
                db.session.commit()
                
                logger.info(f"  ✅ {stats['synced']} synced, {stats['errors']} errors")
                
                # Délai entre les lots (sauf le dernier)
                if batch_num < total_batches - 1:
                    time.sleep(2)
            
            # 7. Mettre à jour les compteurs
            logger.info("\n📊 MISE À JOUR DES COMPTEURS")
            logger.info("-" * 80)
            cj_sync._update_category_counts()
            logger.info("✅ Compteurs mis à jour")
            
            # 8. État final
            logger.info("\n📊 ÉTAT FINAL")
            logger.info("-" * 80)
            total_after, cj_after, published_after = count_current_products()
            logger.info(f"  Produits totaux: {total_after}")
            logger.info(f"  Produits CJ: {cj_after}")
            logger.info(f"  Produits publiés: {published_after}")
            
            # 9. Résumé
            logger.info("\n" + "=" * 80)
            logger.info("✅ RÉCUPÉRATION TERMINÉE")
            logger.info("=" * 80)
            logger.info(f"  Produits synchronisés: {stats['synced']}")
            logger.info(f"  Erreurs: {stats['errors']}")
            logger.info(f"  Nouveaux produits CJ: {cj_after - cj_before}")
            logger.info("=" * 80)
            
            # 10. Lancer l'enrichissement
            logger.info("\n💡 PROCHAINE ÉTAPE:")
            logger.info("  Lancez le script d'enrichissement rapide:")
            logger.info("  python scripts\\fast_enrich_products.py")
            
            return 0
            
        except Exception as e:
            logger.error(f"❌ Erreur fatale: {e}")
            import traceback
            traceback.print_exc()
            return 1


if __name__ == '__main__':
    exit(main())
