"""
Tâches Celery pour la synchronisation automatique des produits
"""
from celery import shared_task
from models.product import Product
from services.api_providers.cj_dropshipping_optimized import CJDropshippingApiOptimized
from extensions import db
import os
import time
import logging

logger = logging.getLogger(__name__)


@shared_task(name='sync_products_daily')
def sync_products_daily():
    """
    Synchronisation quotidienne des produits CJ
    - Mise à jour des prix
    - Mise à jour des stocks
    - Mise à jour des descriptions manquantes
    """
    try:
        cj_api = CJDropshippingApiOptimized(
            email=os.getenv('CJ_EMAIL'),
            password=os.getenv('CJ_PASSWORD')
        )
        
        products = Product.query.filter(
            Product.cj_pid.isnot(None),
            Product.published == True
        ).all()
        
        updated_count = 0
        errors = 0
        
        for product in products:
            try:
                # Récupérer les données à jour
                details = cj_api.get_product_details(product.cj_pid)
                
                if details:
                    # Mettre à jour le prix
                    if details.get('price'):
                        product.price = float(details['price'])
                    
                    # Mettre à jour le stock
                    if details.get('stock') is not None:
                        product.stock = int(details['stock'])
                    
                    # Ajouter description si manquante
                    if not product.description and details.get('description'):
                        product.description = details['description']
                    
                    # Mettre à jour la date de sync
                    from datetime import datetime
                    product.cj_last_sync = datetime.utcnow()
                    
                    updated_count += 1
                
                time.sleep(2)  # Rate limit
                
            except Exception as e:
                logger.error(f"Erreur sync produit {product.id}: {e}")
                errors += 1
        
        db.session.commit()
        
        return {
            'status': 'success',
            'updated': updated_count,
            'total': len(products),
            'errors': errors
        }
        
    except Exception as e:
        logger.error(f"Erreur sync_products_daily: {e}")
        return {
            'status': 'error',
            'message': str(e)
        }


@shared_task(name='sync_reviews_weekly')
def sync_reviews_weekly():
    """Synchronisation hebdomadaire des avis clients"""
    try:
        from models.product_review import ProductReview
        
        cj_api = CJDropshippingApiOptimized(
            email=os.getenv('CJ_EMAIL'),
            password=os.getenv('CJ_PASSWORD')
        )
        
        # Récupérer les produits sans avis ou avec peu d'avis
        products = Product.query.filter(
            Product.cj_pid.isnot(None),
            Product.published == True
        ).limit(200).all()
        
        total_reviews = 0
        products_updated = 0
        
        for product in products:
            try:
                reviews_data = cj_api.get_product_comments(product.cj_pid)
                
                if reviews_data and isinstance(reviews_data, list):
                    for review_data in reviews_data[:10]:  # Max 10 avis par produit
                        cj_review_id = review_data.get('id') or review_data.get('commentId')
                        
                        if cj_review_id:
                            existing = ProductReview.query.filter_by(
                                cj_review_id=str(cj_review_id)
                            ).first()
                            
                            if not existing:
                                review = ProductReview(
                                    product_id=product.id,
                                    cj_review_id=str(cj_review_id),
                                    author_name=review_data.get('userName') or 'Client',
                                    rating=int(review_data.get('star') or 5),
                                    comment=review_data.get('comment') or '',
                                    verified_purchase=True,
                                    is_approved=True
                                )
                                db.session.add(review)
                                total_reviews += 1
                    
                    if total_reviews > 0:
                        products_updated += 1
                
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Erreur sync avis produit {product.id}: {e}")
        
        db.session.commit()
        
        return {
            'status': 'success',
            'reviews_added': total_reviews,
            'products_updated': products_updated
        }
        
    except Exception as e:
        logger.error(f"Erreur sync_reviews_weekly: {e}")
        return {
            'status': 'error',
            'message': str(e)
        }


@shared_task(name='cleanup_old_data')
def cleanup_old_data():
    """Nettoyage mensuel des anciennes données"""
    try:
        from datetime import datetime, timedelta
        
        # Supprimer les produits non publiés depuis > 6 mois
        six_months_ago = datetime.utcnow() - timedelta(days=180)
        
        old_products = Product.query.filter(
            Product.published == False,
            Product.created_at < six_months_ago
        ).all()
        
        deleted_count = len(old_products)
        
        for product in old_products:
            db.session.delete(product)
        
        db.session.commit()
        
        return {
            'status': 'success',
            'deleted_products': deleted_count
        }
        
    except Exception as e:
        logger.error(f"Erreur cleanup_old_data: {e}")
        return {
            'status': 'error',
            'message': str(e)
        }
