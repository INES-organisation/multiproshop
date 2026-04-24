"""
Script de téléchargement des images CJ Dropshipping
Télécharge et optimise les images des produits CJ en local
"""
import sys
import os
from datetime import datetime
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from models.product import Product
from services.image_service import get_image_service
from extensions import db
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def download_product_images(max_products: int = 50, skip_existing: bool = True):
    """
    Télécharger les images des produits CJ
    
    Args:
        max_products: Nombre max de produits à traiter
        skip_existing: Ignorer les produits avec images locales
    """
    
    with app.app_context():
        logger.info("="*70)
        logger.info("📥 TÉLÉCHARGEMENT IMAGES CJ DROPSHIPPING")
        logger.info("="*70)
        logger.info(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Limite: {max_products} produits")
        logger.info(f"Ignorer existants: {skip_existing}")
        
        # Récupérer le service d'images
        image_service = get_image_service()
        
        # Récupérer les produits CJ avec images distantes
        query = Product.query.filter(
            Product.cj_pid.isnot(None),
            Product.cj_pid != '',
            Product.image_url.isnot(None),
            Product.image_url != ''
        )
        
        # Filtrer ceux sans image locale si demandé
        if skip_existing:
            query = query.filter(
                db.or_(
                    Product.local_image_path.is_(None),
                    Product.local_image_path == ''
                )
            )
        
        products = query.limit(max_products).all()
        
        total_products = len(products)
        logger.info(f"\n📦 Produits à traiter: {total_products}")
        
        if total_products == 0:
            logger.info("✅ Aucun produit à traiter")
            return True
        
        # Statistiques
        success_count = 0
        error_count = 0
        skipped_count = 0
        
        # Traiter chaque produit
        for i, product in enumerate(products, 1):
            logger.info(f"\n[{i}/{total_products}] Produit: {product.name[:50]}...")
            logger.info(f"  ID: {product.id}")
            logger.info(f"  CJ PID: {product.cj_pid}")
            logger.info(f"  URL image: {product.image_url[:60]}...")
            
            try:
                # Délai pour éviter surcharge
                if i > 1:
                    time.sleep(1)
                
                # Traiter l'image
                result = image_service.process_product_image(
                    url=product.image_url,
                    product_id=product.id,
                    optimize=True,
                    webp=True,
                    thumbnails=True
                )
                
                if result['success']:
                    # Mettre à jour le produit
                    product.local_image_path = result['original']
                    
                    if result.get('webp'):
                        product.webp_image_path = result['webp']
                    
                    # Stocker les miniatures (JSON)
                    if result.get('thumbnails'):
                        import json
                        product.thumbnail_paths = json.dumps(result['thumbnails'])
                    
                    product.updated_at = datetime.now()
                    db.session.commit()
                    
                    success_count += 1
                    logger.info(f"  ✅ Image téléchargée et optimisée")
                    logger.info(f"     Original: {result['original']}")
                    if result.get('webp'):
                        logger.info(f"     WebP: {result['webp']}")
                    if result.get('thumbnails'):
                        logger.info(f"     Miniatures: {len(result['thumbnails'])}")
                else:
                    error_count += 1
                    logger.error(f"  ❌ Erreur: {result.get('error', 'Inconnue')}")
                    
            except Exception as e:
                error_count += 1
                logger.error(f"  ❌ Exception: {e}")
                db.session.rollback()
        
        # Résumé
        logger.info("\n" + "="*70)
        logger.info("📊 RÉSUMÉ DU TÉLÉCHARGEMENT")
        logger.info("="*70)
        logger.info(f"Total produits: {total_products}")
        logger.info(f"✅ Succès: {success_count}")
        logger.info(f"❌ Erreurs: {error_count}")
        logger.info(f"⏭️ Ignorés: {skipped_count}")
        logger.info(f"Taux de réussite: {(success_count/total_products*100):.1f}%")
        logger.info("="*70)
        
        return error_count == 0


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Télécharger images produits CJ')
    parser.add_argument('max_products', type=int, nargs='?', default=50,
                       help='Nombre max de produits (défaut: 50)')
    parser.add_argument('--all', action='store_true',
                       help='Télécharger même si image locale existe')
    
    args = parser.parse_args()
    
    try:
        success = download_product_images(
            max_products=args.max_products,
            skip_existing=not args.all
        )
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
