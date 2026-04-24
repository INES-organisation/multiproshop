"""
CRON Job - Synchronisation Stock CJ Dropshipping
Exécution quotidienne (tous les jours à 3h du matin)
Met à jour le stock de tous les produits CJ depuis l'API
"""
import sys
import os
from datetime import datetime
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from models.product import Product
from models.product_variant import ProductVariant
from models.api_provider import ApiProvider
from services.api_providers.cj_dropshipping_optimized import CJDropshippingProvider
from services.admin_notifications import AdminNotificationService
from extensions import db
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def sync_product_stock(cj_api, product):
    """
    Synchroniser le stock d'un produit depuis CJ
    
    Args:
        cj_api: Instance CJDropshippingProvider
        product: Produit à synchroniser
        
    Returns:
        dict: Résultat de la synchronisation
    """
    try:
        if not product.cj_pid:
            return {'success': False, 'error': 'Pas de cj_pid'}
        
        # Récupérer les infos du produit depuis CJ
        result = cj_api.get_product_details(product.cj_pid)
        
        # Gérer le rate limiting
        if not result:
            return {'success': False, 'error': 'Pas de réponse API'}
        
        if isinstance(result, dict) and not result.get('success', True):
            error = result.get('error', 'Erreur inconnue')
            # Si rate limit, attendre et réessayer
            if '429' in str(error):
                logger.warning(f"  ⚠️ Rate limit atteint, attente 5 secondes...")
                time.sleep(5)
                result = cj_api.get_product_details(product.cj_pid)
                if not result or (isinstance(result, dict) and not result.get('success', True)):
                    AdminNotificationService.notify_cj_api_down('Rate limit persistant sur API CJ')
                    return {'success': False, 'error': 'Rate limit persistant'}
            else:
                return {'success': False, 'error': error}
        
        # Extraire les données du produit
        if isinstance(result, dict) and 'data' in result:
            product_data = result.get('data', {})
        else:
            product_data = result if isinstance(result, dict) else {}
        
        variants = product_data.get('variants', [])
        
        updated_count = 0
        total_stock = 0
        
        # Mettre à jour le stock de chaque variante
        for variant_data in variants:
            vid = variant_data.get('vid')
            stock = variant_data.get('stock', 0)
            
            if not vid:
                continue
            
            # Trouver la variante locale
            variant = ProductVariant.query.filter_by(
                product_id=product.id,
                cj_vid=vid
            ).first()
            
            if variant:
                old_stock = variant.stock
                variant.stock = stock
                variant.updated_at = datetime.now()
                updated_count += 1
                total_stock += stock
                
                if old_stock != stock:
                    logger.info(f"  Variante {vid}: {old_stock} → {stock}")
        
        # Mettre à jour le stock total du produit
        if updated_count > 0:
            product.stock = total_stock
            product.updated_at = datetime.now()
            db.session.commit()
            
            return {
                'success': True,
                'updated_variants': updated_count,
                'total_stock': total_stock
            }
        else:
            return {'success': False, 'error': 'Aucune variante trouvée'}
            
    except Exception as e:
        logger.error(f"Erreur sync stock produit {product.id}: {e}")
        return {'success': False, 'error': str(e)}


def sync_all_stock(max_products=50):
    """
    Synchroniser le stock de produits CJ
    
    Args:
        max_products: Nombre max de produits à synchroniser (défaut: 5)
    """
    
    with app.app_context():
        logger.info("="*70)
        logger.info("🔄 SYNCHRONISATION STOCK CJ DROPSHIPPING")
        logger.info("="*70)
        logger.info(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Limite: {max_products} produits")
        
        # Récupérer le provider CJ
        provider = ApiProvider.query.filter_by(name='CJ Dropshipping').first()
        
        if not provider:
            logger.error("❌ Provider CJ Dropshipping non trouvé")
            return False
        
        logger.info(f"✅ Provider: {provider.name}")
        
        # Créer l'instance API
        cj_api = CJDropshippingProvider(provider)
        
        # Récupérer les produits CJ (limité)
        products = Product.query.filter(
            Product.cj_pid.isnot(None),
            Product.cj_pid != ''
        ).limit(max_products).all()
        
        total_products = len(products)
        logger.info(f"\n📦 Produits à synchroniser: {total_products}")
        
        if total_products == 0:
            logger.warning("⚠️ Aucun produit CJ trouvé")
            return True
        
        # Statistiques
        success_count = 0
        error_count = 0
        updated_variants = 0
        
        # Synchroniser chaque produit
        for i, product in enumerate(products, 1):
            logger.info(f"\n[{i}/{total_products}] Produit: {product.name}")
            logger.info(f"  CJ PID: {product.cj_pid}")
            
            # Délai entre chaque requête pour éviter rate limiting
            if i > 1:
                time.sleep(0.5)  # 0.5 seconde entre chaque produit
            
            result = sync_product_stock(cj_api, product)
            
            if result.get('success'):
                success_count += 1
                updated_variants += result.get('updated_variants', 0)
                logger.info(f"  ✅ Stock mis à jour: {result.get('total_stock')} unités")
            else:
                error_count += 1
                logger.error(f"  ❌ Erreur: {result.get('error')}")
        
        # Résumé
        logger.info("\n" + "="*70)
        logger.info("📊 RÉSUMÉ DE LA SYNCHRONISATION")
        logger.info("="*70)
        logger.info(f"Total produits: {total_products}")
        logger.info(f"✅ Succès: {success_count}")
        logger.info(f"❌ Erreurs: {error_count}")
        logger.info(f"🔄 Variantes mises à jour: {updated_variants}")
        logger.info(f"Taux de réussite: {(success_count/total_products*100):.1f}%")
        logger.info("="*70)
        
        return error_count == 0


if __name__ == '__main__':
    try:
        success = sync_all_stock()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
