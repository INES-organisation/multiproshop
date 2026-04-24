"""
Tâches Celery pour synchronisation automatique des variantes CJ
Gestion intelligente du rate limit avec retry automatique
"""
from celery_app import celery
from app import app
from models.product import Product
from models.product_variant import ProductVariant
from services.api_providers.cj_dropshipping_optimized import CJDropshippingApiOptimized
from extensions import db
from datetime import datetime
import logging
import os
import time

logger = logging.getLogger(__name__)


@celery.task(
    name='tasks.variant_sync_tasks.sync_product_variants',
    bind=True,
    max_retries=5,
    default_retry_delay=300  # 5 minutes entre les retries
)
def sync_product_variants(self, product_id):
    """
    Synchroniser les variantes d'un produit CJ
    Avec retry automatique en cas de rate limit
    
    Args:
        product_id: ID du produit à synchroniser
    """
    try:
        with app.app_context():
            product = Product.query.get(product_id)
            
            if not product or not product.cj_pid:
                logger.warning(f"[Celery] Produit {product_id} non trouvé ou sans CJ PID")
                return {'success': False, 'reason': 'no_cj_pid'}
            
            logger.info(f"[Celery] Sync variantes pour: {product.name[:50]}...")
            
            # Créer l'API CJ
            cj_api = CJDropshippingApiOptimized(
                email=os.getenv('CJ_EMAIL'),
                password=os.getenv('CJ_PASSWORD')
            )
            
            # Récupérer les variantes
            variants_data = cj_api.get_product_variants(product.cj_pid)
            
            if not variants_data or 'data' not in variants_data:
                logger.warning(f"[Celery] Pas de variantes pour {product.cj_pid}")
                return {'success': False, 'reason': 'no_variants'}
            
            # Extraire la liste des variantes
            variants_list = variants_data.get('data', [])
            if isinstance(variants_list, dict):
                variants_list = variants_list.get('list', [])
            
            if not variants_list:
                logger.warning(f"[Celery] Liste variantes vide pour {product.cj_pid}")
                return {'success': False, 'reason': 'empty_list'}
            
            # Synchroniser les variantes
            variants_created = 0
            variants_updated = 0
            
            for variant_data in variants_list:
                vid = variant_data.get('vid')
                if not vid:
                    continue
                
                existing_variant = ProductVariant.query.filter_by(
                    product_id=product.id,
                    cj_vid=vid
                ).first()
                
                stock = variant_data.get('variantStock') or variant_data.get('inventoryNum', 0)
                
                if existing_variant:
                    # Mettre à jour
                    existing_variant.variant_key = variant_data.get('variantKey', '')
                    existing_variant.price = float(variant_data.get('variantSellPrice', 0))
                    existing_variant.suggested_price = float(variant_data.get('variantSugSellPrice', 0))
                    existing_variant.stock = int(stock) if stock else 0
                    existing_variant.image_url = variant_data.get('variantImage', '')
                    existing_variant.weight = int(variant_data.get('variantWeight', 0)) if variant_data.get('variantWeight') else 0
                    existing_variant.sku = variant_data.get('variantSku', '')
                    existing_variant.updated_at = datetime.utcnow()
                    variants_updated += 1
                else:
                    # Créer
                    new_variant = ProductVariant(
                        product_id=product.id,
                        cj_vid=vid,
                        variant_key=variant_data.get('variantKey', ''),
                        price=float(variant_data.get('variantSellPrice', 0)),
                        suggested_price=float(variant_data.get('variantSugSellPrice', 0)),
                        stock=int(stock) if stock else 0,
                        image_url=variant_data.get('variantImage', ''),
                        weight=int(variant_data.get('variantWeight', 0)) if variant_data.get('variantWeight') else 0,
                        sku=variant_data.get('variantSku', ''),
                        active=True
                    )
                    db.session.add(new_variant)
                    variants_created += 1
            
            db.session.commit()
            
            # Mettre à jour le stock total
            product.update_stock_from_variants()
            db.session.commit()
            
            logger.info(f"[Celery] ✅ {variants_created} créées, {variants_updated} mises à jour")
            
            return {
                'success': True,
                'product_id': product_id,
                'variants_created': variants_created,
                'variants_updated': variants_updated,
                'total_stock': product.stock
            }
            
    except Exception as e:
        logger.error(f"[Celery] Erreur sync variantes produit {product_id}: {e}")
        
        # Si c'est un rate limit, retry après 5 minutes
        if 'rate limit' in str(e).lower() or 'Rate limit' in str(e):
            logger.warning(f"[Celery] Rate limit détecté - retry dans 5 minutes")
            raise self.retry(exc=e, countdown=300)
        
        # Autres erreurs, retry avec backoff exponentiel
        raise self.retry(exc=e)


@celery.task(
    name='tasks.variant_sync_tasks.sync_all_variants',
    bind=True
)
def sync_all_variants(self, batch_size=50, delay_between_batches=600):
    """
    Synchroniser les variantes de tous les produits CJ
    Par lots avec délais pour éviter le rate limit
    
    Args:
        batch_size: Nombre de produits par lot (défaut: 50)
        delay_between_batches: Délai entre les lots en secondes (défaut: 600 = 10 min)
    """
    try:
        with app.app_context():
            logger.info("[Celery] Début synchronisation complète des variantes")
            
            # Récupérer tous les produits CJ publiés
            products = Product.query.filter(
                Product.cj_pid.isnot(None),
                Product.published == True
            ).all()
            
            total_products = len(products)
            logger.info(f"[Celery] {total_products} produits CJ à synchroniser")
            
            # Diviser en lots
            batches = [products[i:i + batch_size] for i in range(0, total_products, batch_size)]
            
            stats = {
                'total': total_products,
                'processed': 0,
                'success': 0,
                'failed': 0
            }
            
            for batch_index, batch in enumerate(batches, 1):
                logger.info(f"[Celery] Traitement lot {batch_index}/{len(batches)} ({len(batch)} produits)")
                
                # Lancer les tâches pour ce lot
                for product in batch:
                    try:
                        # Lancer la tâche asynchrone avec délai progressif
                        sync_product_variants.apply_async(
                            args=[product.id],
                            countdown=batch_index * 3  # 3s de délai par produit dans le lot
                        )
                        stats['processed'] += 1
                    except Exception as e:
                        logger.error(f"[Celery] Erreur lancement tâche pour produit {product.id}: {e}")
                        stats['failed'] += 1
                
                # Attendre entre les lots (sauf pour le dernier)
                if batch_index < len(batches):
                    logger.info(f"[Celery] Pause de {delay_between_batches}s avant le prochain lot...")
                    time.sleep(delay_between_batches)
            
            logger.info(f"[Celery] ✅ Synchronisation lancée: {stats['processed']} tâches créées")
            
            return stats
            
    except Exception as e:
        logger.error(f"[Celery] Erreur sync_all_variants: {e}")
        raise


@celery.task(
    name='tasks.variant_sync_tasks.sync_missing_variants',
    bind=True
)
def sync_missing_variants(self):
    """
    Synchroniser uniquement les produits sans variantes
    Utile pour compléter une synchronisation partielle
    """
    try:
        with app.app_context():
            logger.info("[Celery] Recherche des produits sans variantes...")
            
            # Trouver les produits CJ publiés sans variantes
            products_without_variants = db.session.query(Product).filter(
                Product.cj_pid.isnot(None),
                Product.published == True,
                ~Product.id.in_(
                    db.session.query(ProductVariant.product_id).distinct()
                )
            ).all()
            
            total = len(products_without_variants)
            logger.info(f"[Celery] {total} produits sans variantes trouvés")
            
            if total == 0:
                return {'success': True, 'message': 'Tous les produits ont des variantes'}
            
            # Lancer les tâches avec délais
            for index, product in enumerate(products_without_variants, 1):
                sync_product_variants.apply_async(
                    args=[product.id],
                    countdown=index * 5  # 5s entre chaque produit
                )
            
            logger.info(f"[Celery] ✅ {total} tâches de synchronisation lancées")
            
            return {
                'success': True,
                'products_to_sync': total
            }
            
    except Exception as e:
        logger.error(f"[Celery] Erreur sync_missing_variants: {e}")
        raise


@celery.task(name='tasks.variant_sync_tasks.update_stock_from_variants')
def update_stock_from_variants():
    """
    Mettre à jour le stock total de tous les produits depuis leurs variantes
    Tâche de maintenance quotidienne
    """
    try:
        with app.app_context():
            logger.info("[Celery] Mise à jour des stocks depuis les variantes")
            
            products_with_variants = Product.query.join(ProductVariant).distinct().all()
            
            updated = 0
            for product in products_with_variants:
                if product.update_stock_from_variants():
                    updated += 1
            
            db.session.commit()
            
            logger.info(f"[Celery] ✅ {updated} stocks mis à jour")
            
            return {
                'success': True,
                'updated': updated
            }
            
    except Exception as e:
        logger.error(f"[Celery] Erreur update_stock_from_variants: {e}")
        raise
