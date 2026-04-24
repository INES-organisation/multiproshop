"""
Script pour synchroniser les avis clients depuis l'API CJ Dropshipping
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from app import create_app
from models.product import Product
from models.product_review import ProductReview
from services.api_providers.cj_dropshipping_optimized import CJDropshippingApiOptimized
from extensions import db
import logging
import time
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

app = create_app()

def sync_product_reviews(product, cj_api):
    """Synchroniser les avis d'un produit depuis CJ"""
    try:
        logger.info(f"[{product.id}] {product.name[:50]}...")
        
        # Récupérer les avis depuis l'API CJ
        reviews_data = cj_api.get_product_comments(product.cj_pid)
        
        if not reviews_data or not isinstance(reviews_data, list):
            logger.warning(f"  ⚠️  Pas d'avis disponibles")
            return 0
        
        synced_count = 0
        
        for review_data in reviews_data[:20]:  # Limiter à 20 avis par produit
            # Vérifier si l'avis existe déjà
            cj_review_id = review_data.get('id') or review_data.get('commentId')
            
            if cj_review_id:
                existing_review = ProductReview.query.filter_by(
                    cj_review_id=str(cj_review_id)
                ).first()
                
                if existing_review:
                    continue  # Avis déjà synchronisé
            
            # Créer le nouvel avis
            review = ProductReview(
                product_id=product.id,
                cj_review_id=str(cj_review_id) if cj_review_id else None,
                author_name=review_data.get('userName') or review_data.get('author') or 'Client',
                rating=int(review_data.get('star') or review_data.get('rating') or 5),
                title=review_data.get('title'),
                comment=review_data.get('comment') or review_data.get('content') or '',
                verified_purchase=True,
                is_approved=True
            )
            
            # Date de l'avis
            review_date_str = review_data.get('createTime') or review_data.get('date')
            if review_date_str:
                try:
                    review.review_date = datetime.fromisoformat(review_date_str.replace('Z', '+00:00'))
                except:
                    pass
            
            # Images de l'avis
            images = review_data.get('images') or review_data.get('photos') or []
            if images:
                review.set_images_list(images)
            
            db.session.add(review)
            synced_count += 1
        
        if synced_count > 0:
            db.session.commit()
            logger.info(f"  ✅ {synced_count} avis synchronisés")
        
        return synced_count
        
    except Exception as e:
        logger.error(f"  ❌ Erreur: {e}")
        db.session.rollback()
        return 0

def main():
    with app.app_context():
        print("\n" + "="*70)
        print("SYNCHRONISATION DES AVIS CLIENTS DEPUIS CJ")
        print("="*70 + "\n")
        
        # Récupérer les produits CJ
        products = Product.query.filter(
            Product.cj_pid.isnot(None),
            Product.published == True
        ).limit(100).all()  # Limiter à 100 produits pour le test
        
        total = len(products)
        print(f"Produits à traiter: {total}\n")
        
        if total == 0:
            print("❌ Aucun produit CJ trouvé")
            return
        
        # Créer l'API CJ
        cj_api = CJDropshippingApiOptimized(
            email=os.getenv('CJ_EMAIL'),
            password=os.getenv('CJ_PASSWORD')
        )
        
        total_reviews = 0
        products_with_reviews = 0
        
        for i, product in enumerate(products, 1):
            print(f"\n[{i}/{total}] ", end='')
            
            count = sync_product_reviews(product, cj_api)
            
            if count > 0:
                total_reviews += count
                products_with_reviews += 1
            
            # Délai pour éviter le rate limit
            if i < total:
                time.sleep(2)
            
            # Progression tous les 20 produits
            if i % 20 == 0:
                print(f"\n{'='*70}")
                print(f"PROGRESSION: {i}/{total} ({round(i/total*100, 1)}%)")
                print(f"Avis synchronisés: {total_reviews}")
                print(f"Produits avec avis: {products_with_reviews}")
                print(f"{'='*70}\n")
        
        print("\n" + "="*70)
        print("RÉSUMÉ FINAL")
        print("="*70)
        print(f"Produits traités: {total}")
        print(f"✅ Produits avec avis: {products_with_reviews}")
        print(f"📝 Total avis synchronisés: {total_reviews}")
        print(f"Moyenne: {round(total_reviews/products_with_reviews, 1) if products_with_reviews > 0 else 0} avis/produit")
        print("="*70 + "\n")

if __name__ == '__main__':
    main()
