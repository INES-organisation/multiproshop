"""
Tâches Celery pour synchronisation CJ Dropshipping
Exécution asynchrone des synchronisations
"""
from celery_app import celery
from app import app
from models.product import Product
from models.product_variant import ProductVariant
from models.order import Order
from models.api_provider import ApiProvider
from services.api_providers.cj_dropshipping_optimized import CJDropshippingProvider
from services.cj_sync_service import CjSyncService
from services.cj_order_service import CjOrderService
from services.admin_notifications import AdminNotificationService
from extensions import db
import logging
import time

logger = logging.getLogger(__name__)


@celery.task(name='tasks.cj_sync_tasks.sync_products_task', bind=True, max_retries=3)
def sync_products_task(self, category_id=None, limit=100):
    """
    Tâche asynchrone: Synchroniser les produits CJ
    
    Args:
        category_id: ID catégorie CJ (optionnel)
        limit: Nombre max de produits
    """
    try:
        with app.app_context():
            logger.info(f"[Celery] Début sync produits (category={category_id}, limit={limit})")
            
            # Récupérer le provider CJ
            provider = ApiProvider.query.filter_by(name='CJ Dropshipping').first()
            if not provider:
                raise ValueError("Provider CJ Dropshipping non trouvé")
            
            # Créer les services
            cj_api = CJDropshippingProvider(provider)
            sync_service = CjSyncService(cj_api)
            
            # Synchroniser
            result = sync_service.sync_products(
                category_id=category_id,
                limit=limit
            )
            
            if result.get('success'):
                logger.info(f"[Celery] ✅ Sync produits terminée: {result.get('synced')} produits")
                return {
                    'status': 'success',
                    'synced': result.get('synced'),
                    'errors': result.get('errors', [])
                }
            else:
                error_msg = result.get('message', 'Erreur inconnue')
                logger.error(f"[Celery] ❌ Erreur sync produits: {error_msg}")
                
                # Notifier admin
                AdminNotificationService.notify_cj_sync_failure(
                    error_type='PRODUCTS',
                    error_message=error_msg,
                    details={'category_id': category_id, 'limit': limit}
                )
                
                raise Exception(error_msg)
                
    except Exception as e:
        logger.error(f"[Celery] Exception sync_products_task: {e}")
        
        # Retry avec backoff exponentiel
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


@celery.task(name='tasks.cj_sync_tasks.sync_stock_task', bind=True, max_retries=3)
def sync_stock_task(self, product_ids=None):
    """
    Tâche asynchrone: Synchroniser le stock CJ
    
    Args:
        product_ids: Liste IDs produits (optionnel, sinon tous)
    """
    try:
        with app.app_context():
            logger.info(f"[Celery] Début sync stock (products={len(product_ids) if product_ids else 'all'})")
            
            # Récupérer le provider CJ
            provider = ApiProvider.query.filter_by(name='CJ Dropshipping').first()
            if not provider:
                raise ValueError("Provider CJ Dropshipping non trouvé")
            
            # Créer les services
            cj_api = CJDropshippingProvider(provider)
            sync_service = CjSyncService(cj_api)
            
            # Synchroniser
            result = sync_service.sync_stock()
            
            if result.get('success'):
                logger.info(f"[Celery] ✅ Sync stock terminée: {result.get('updated')} produits")
                return {
                    'status': 'success',
                    'updated': result.get('updated'),
                    'errors': result.get('errors', [])
                }
            else:
                error_msg = result.get('message', 'Erreur inconnue')
                logger.error(f"[Celery] ❌ Erreur sync stock: {error_msg}")
                
                # Notifier admin
                AdminNotificationService.notify_cj_sync_failure(
                    error_type='STOCK',
                    error_message=error_msg
                )
                
                raise Exception(error_msg)
                
    except Exception as e:
        logger.error(f"[Celery] Exception sync_stock_task: {e}")
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


@celery.task(name='tasks.cj_sync_tasks.sync_orders_task', bind=True, max_retries=3)
def sync_orders_task(self):
    """
    Tâche asynchrone: Synchroniser les commandes CJ
    """
    try:
        with app.app_context():
            logger.info("[Celery] Début sync commandes")
            
            # Récupérer le provider CJ
            provider = ApiProvider.query.filter_by(name='CJ Dropshipping').first()
            if not provider:
                raise ValueError("Provider CJ Dropshipping non trouvé")
            
            # Créer les services
            cj_api = CJDropshippingProvider(provider)
            order_service = CjOrderService(cj_api)
            
            # Synchroniser toutes les commandes en attente
            result = order_service.sync_all_pending_orders()
            
            logger.info(f"[Celery] ✅ Sync commandes terminée: {result.get('synced', 0)} commandes")
            
            return {
                'status': 'success',
                'synced': result.get('synced', 0),
                'errors': result.get('errors', [])
            }
                
    except Exception as e:
        logger.error(f"[Celery] Exception sync_orders_task: {e}")
        
        # Notifier admin
        AdminNotificationService.notify_cj_sync_failure(
            error_type='ORDERS',
            error_message=str(e)
        )
        
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


@celery.task(name='tasks.cj_sync_tasks.sync_single_product', bind=True, max_retries=3)
def sync_single_product_task(self, cj_pid):
    """
    Tâche asynchrone: Synchroniser un seul produit
    
    Args:
        cj_pid: Product ID CJ
    """
    try:
        with app.app_context():
            logger.info(f"[Celery] Sync produit {cj_pid}")
            
            # Récupérer le provider CJ
            provider = ApiProvider.query.filter_by(name='CJ Dropshipping').first()
            if not provider:
                raise ValueError("Provider CJ Dropshipping non trouvé")
            
            # Créer les services
            cj_api = CJDropshippingProvider(provider)
            
            # Récupérer les détails du produit
            result = cj_api.get_product_details(cj_pid)
            
            if result and result.get('success'):
                product_data = result.get('data', {})
                
                # Synchroniser le produit
                sync_service = CjSyncService(cj_api)
                sync_service._sync_product(product_data)
                db.session.commit()
                
                logger.info(f"[Celery] ✅ Produit {cj_pid} synchronisé")
                
                return {
                    'status': 'success',
                    'cj_pid': cj_pid
                }
            else:
                raise Exception(f"Impossible de récupérer produit {cj_pid}")
                
    except Exception as e:
        logger.error(f"[Celery] Exception sync_single_product: {e}")
        db.session.rollback()
        raise self.retry(exc=e, countdown=30 * (2 ** self.request.retries))


@celery.task(name='tasks.cj_sync_tasks.enrich_product_task', bind=True, max_retries=3)
def enrich_product_task(self, product_id):
    """
    Tâche asynchrone: Enrichir un produit avec détails complets
    Récupère: description, variantes, stock, avis, méthodes de livraison
    
    Args:
        product_id: ID produit local
    """
    try:
        with app.app_context():
            product = Product.query.get(product_id)
            if not product or not product.cj_pid:
                raise ValueError(f"Produit {product_id} non trouvé ou sans cj_pid")
            
            logger.info(f"[Celery] Enrichissement complet produit {product.cj_pid}")
            
            # Récupérer le provider CJ
            provider = ApiProvider.query.filter_by(name='CJ Dropshipping').first()
            if not provider:
                raise ValueError("Provider CJ Dropshipping non trouvé")
            
            # Créer les services
            cj_api = CJDropshippingProvider(provider)
            sync_service = CjSyncService(cj_api)
            
            # 1. Enrichir avec détails complets (description, avis)
            result = sync_service.enrich_product(product.cj_pid)
            
            # 2. Synchroniser les variantes
            from services.cj_variant_sync_service import CjVariantSyncService
            variant_service = CjVariantSyncService(cj_api)
            
            try:
                variant_result = variant_service.sync_product_variants(product_id)
                if variant_result.get('success'):
                    # Mettre à jour le stock principal depuis les variantes
                    product.update_stock_from_variants()
                    db.session.commit()
                    logger.info(f"[Celery] ✅ Variantes synchronisées: {variant_result.get('total_variants', 0)}")
            except Exception as e:
                logger.warning(f"[Celery] Erreur sync variantes (non bloquant): {e}")
            
            if result.get('success'):
                logger.info(f"[Celery] ✅ Produit {product.cj_pid} enrichi complètement")
                return {
                    'status': 'success',
                    'product_id': product_id,
                    'has_variants': variant_result.get('success', False) if 'variant_result' in locals() else False
                }
            else:
                raise Exception(result.get('message', 'Erreur enrichissement'))
                
    except Exception as e:
        logger.error(f"[Celery] Exception enrich_product: {e}")
        # Retry avec backoff
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


@celery.task(name='tasks.cj_sync_tasks.enrich_all_products_task', bind=True)
def enrich_all_products_task(self, batch_size=20, delay_between_products=1):
    """
    Tâche asynchrone: Enrichir tous les produits CJ sans variantes
    Lance des tâches d'enrichissement pour chaque produit
    OPTIMISÉ: batch_size=20, délai=1s pour aller plus vite
    
    Args:
        batch_size: Nombre de produits à traiter par lot (défaut: 20)
        delay_between_products: Délai en secondes entre chaque produit (défaut: 1s)
    """
    try:
        with app.app_context():
            logger.info("[Celery] Début enrichissement masse produits")
            
            # Trouver les produits CJ publiés sans variantes
            products_without_variants = db.session.query(Product).filter(
                Product.cj_pid.isnot(None),
                Product.published == True,
                ~Product.id.in_(
                    db.session.query(ProductVariant.product_id).distinct()
                )
            ).all()
            
            total = len(products_without_variants)
            logger.info(f"[Celery] {total} produits à enrichir")
            
            if total == 0:
                return {
                    'status': 'success',
                    'message': 'Tous les produits sont déjà enrichis',
                    'total': 0
                }
            
            # Lancer les tâches d'enrichissement avec délais
            launched = 0
            for index, product in enumerate(products_without_variants, 1):
                try:
                    enrich_product_task.apply_async(
                        args=[product.id],
                        countdown=index * delay_between_products
                    )
                    launched += 1
                    
                    if launched % batch_size == 0:
                        logger.info(f"[Celery] {launched}/{total} tâches lancées")
                        
                except Exception as e:
                    logger.error(f"[Celery] Erreur lancement enrichissement produit {product.id}: {e}")
            
            logger.info(f"[Celery] ✅ {launched} tâches d'enrichissement lancées")
            
            return {
                'status': 'success',
                'message': f'{launched} produits en cours d\'enrichissement',
                'total': launched
            }
            
    except Exception as e:
        logger.error(f"[Celery] Exception enrich_all_products: {e}")
        return {
            'status': 'error',
            'message': str(e)
        }
