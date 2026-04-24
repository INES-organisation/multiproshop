"""
CRON Job - Synchronisation Nouveaux Produits CJ
Exécution hebdomadaire (tous les lundis à 2h du matin)
Récupère et importe les nouveaux produits CJ
"""
import sys
import os
from datetime import datetime
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from models.product import Product
from models.category import Category
from models.api_provider import ApiProvider
from services.api_providers.cj_dropshipping_optimized import CJDropshippingProvider
from services.pricing_service import PricingService
from services.admin_notifications import AdminNotificationService
from extensions import db
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def import_new_products(cj_api, category_id=None, max_products=100):
    """
    Importer de nouveaux produits depuis CJ
    
    Args:
        cj_api: Instance CJDropshippingProvider
        category_id: ID catégorie CJ (optionnel)
        max_products: Nombre max de produits à importer
        
    Returns:
        dict: Résultat de l'import
    """
    try:
        # Récupérer la liste des produits depuis CJ
        result = cj_api.get_product_list(
            page_num=1,
            page_size=max_products,
            category_id=category_id
        )
        
        if not result.get('success'):
            error_msg = result.get('error', 'Erreur inconnue')
            logger.error(f"Erreur récupération liste produits: {error_msg}")
            AdminNotificationService.notify_cj_sync_failure(
                error_type='PRODUCTS',
                error_message=error_msg,
                details={'category_id': category_id, 'max_products': max_products}
            )
            return {'success': False, 'error': error_msg}
        
        products_data = result.get('data', {}).get('list', [])
        
        if not products_data:
            return {'success': True, 'imported': 0, 'skipped': 0}
        
        imported_count = 0
        skipped_count = 0
        
        pricing_service = PricingService()
        
        for product_data in products_data:
            pid = product_data.get('pid')
            
            if not pid:
                skipped_count += 1
                continue
            
            # Vérifier si le produit existe déjà
            existing = Product.query.filter_by(cj_pid=pid).first()
            
            if existing:
                logger.info(f"  ⏭️ Produit {pid} existe déjà")
                skipped_count += 1
                continue
            
            # Créer le nouveau produit
            try:
                # Délai pour éviter rate limiting
                time.sleep(0.5)
                
                # Récupérer les détails complets
                details_result = cj_api.get_product_details(pid)
                
                if not details_result.get('success'):
                    logger.warning(f"  ⚠️ Impossible de récupérer détails {pid}")
                    skipped_count += 1
                    continue
                
                full_data = details_result.get('data', {})
                
                # Calculer le prix de vente
                cj_price = float(full_data.get('sellPrice', 0))
                sell_price = pricing_service.calculate_sell_price(cj_price)
                
                # Créer le produit
                product = Product(
                    name=full_data.get('productNameEn', 'Produit CJ'),
                    description=full_data.get('description', ''),
                    price=sell_price,
                    compare_price=pricing_service.calculate_compare_price(sell_price),
                    stock=full_data.get('stock', 0),
                    image_url=full_data.get('productImage', ''),
                    cj_pid=pid,
                    cj_price=cj_price,
                    is_active=True,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                
                # Associer à une catégorie si possible
                category_name = full_data.get('categoryName')
                if category_name:
                    category = Category.query.filter_by(name=category_name).first()
                    if category:
                        product.category_id = category.id
                
                db.session.add(product)
                db.session.commit()
                
                logger.info(f"  ✅ Produit {pid} importé: {product.name}")
                imported_count += 1
                
            except Exception as e:
                logger.error(f"  ❌ Erreur import produit {pid}: {e}")
                db.session.rollback()
                skipped_count += 1
        
        return {
            'success': True,
            'imported': imported_count,
            'skipped': skipped_count
        }
        
    except Exception as e:
        logger.error(f"Exception import_new_products: {e}")
        AdminNotificationService.notify_cj_sync_failure(
            error_type='PRODUCTS',
            error_message=str(e),
            details={'category_id': category_id, 'max_products': max_products}
        )
        return {'success': False, 'error': str(e)}


def sync_new_products():
    """Synchroniser les nouveaux produits CJ"""
    
    with app.app_context():
        logger.info("="*70)
        logger.info("🔄 SYNCHRONISATION NOUVEAUX PRODUITS CJ")
        logger.info("="*70)
        logger.info(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Récupérer le provider CJ
        provider = ApiProvider.query.filter_by(name='CJ Dropshipping').first()
        
        if not provider:
            logger.error("❌ Provider CJ Dropshipping non trouvé")
            return False
        
        logger.info(f"✅ Provider: {provider.name}")
        
        # Créer l'instance API
        cj_api = CJDropshippingProvider(provider)
        
        # Compter les produits actuels
        current_count = Product.query.filter(
            Product.cj_pid.isnot(None),
            Product.cj_pid != ''
        ).count()
        
        logger.info(f"\n📦 Produits CJ actuels: {current_count}")
        logger.info(f"🔍 Recherche de nouveaux produits...")
        logger.info("✅ Limité à 100 produits par exécution")
        
        # Importer les nouveaux produits (limité à 100)
        result = import_new_products(cj_api, max_products=100)
        
        if result.get('success'):
            imported = result.get('imported', 0)
            skipped = result.get('skipped', 0)
            
            logger.info("\n" + "="*70)
            logger.info("📊 RÉSUMÉ DE LA SYNCHRONISATION")
            logger.info("="*70)
            logger.info(f"Produits actuels: {current_count}")
            logger.info(f"✅ Nouveaux importés: {imported}")
            logger.info(f"⏭️ Ignorés (déjà existants): {skipped}")
            logger.info(f"📦 Total après import: {current_count + imported}")
            logger.info("="*70)
            
            return True
        else:
            logger.error(f"\n❌ Erreur: {result.get('error')}")
            return False


if __name__ == '__main__':
    try:
        success = sync_new_products()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
