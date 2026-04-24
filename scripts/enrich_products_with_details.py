"""
Script pour enrichir les produits avec les détails complets depuis CJ API
Récupère : descriptions, spécifications, images supplémentaires, avis, méthodes de livraison
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from app import create_app
from models.product import Product
from services.api_providers.cj_dropshipping_optimized import CJDropshippingApiOptimized
from extensions import db
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

app = create_app()

def enrich_product_details(product, cj_api):
    """Enrichir un produit avec tous les détails depuis CJ API"""
    try:
        logger.info(f"Enrichissement: {product.name[:50]}...")
        
        # Récupérer les détails complets du produit
        product_details = cj_api.get_product_details(product.cj_pid)
        
        if not product_details or 'data' not in product_details:
            logger.warning(f"  ⚠️  Pas de détails pour {product.cj_pid}")
            return False
        
        data = product_details['data']
        
        # Mise à jour de la description
        description = data.get('description') or data.get('productDescEn') or data.get('productDesc')
        if description:
            product.description = description
            logger.info(f"  ✓ Description ajoutée ({len(description)} chars)")
        
        # Mise à jour des spécifications
        specs = data.get('specifications') or data.get('productSpec')
        if specs:
            import json
            product.specifications = json.dumps(specs, ensure_ascii=False)
            logger.info(f"  ✓ Spécifications ajoutées")
        
        # Mise à jour des images supplémentaires
        images = data.get('productImage') or data.get('images') or []
        if isinstance(images, str):
            images = [images]
        if images and len(images) > 1:
            product.set_images_list(images[1:])
            logger.info(f"  ✓ {len(images)-1} images supplémentaires")
        
        # Mise à jour du poids et dimensions
        if data.get('productWeight'):
            product.product_weight = str(data.get('productWeight'))
        
        if data.get('packLength'):
            product.length = float(data.get('packLength', 0))
        if data.get('packWidth'):
            product.width = float(data.get('packWidth', 0))
        if data.get('packHeight'):
            product.height = float(data.get('packHeight', 0))
        
        # Mise à jour du matériau
        if data.get('material'):
            product.material = data.get('material')
        
        # Mise à jour des données brutes
        import json
        product.cj_raw_data = json.dumps(data, ensure_ascii=False)
        
        db.session.commit()
        logger.info(f"  ✅ Produit enrichi avec succès")
        return True
        
    except Exception as e:
        logger.error(f"  ❌ Erreur: {e}")
        db.session.rollback()
        return False

def main():
    with app.app_context():
        print("\n" + "="*70)
        print("ENRICHISSEMENT DES PRODUITS AVEC DÉTAILS COMPLETS")
        print("="*70 + "\n")
        
        # Compter les produits sans description
        products_without_desc = Product.query.filter(
            Product.cj_pid.isnot(None),
            Product.published == True,
            db.or_(
                Product.description.is_(None),
                Product.description == ''
            )
        ).all()
        
        total = len(products_without_desc)
        print(f"Produits à enrichir: {total}\n")
        
        if total == 0:
            print("✅ Tous les produits ont déjà des descriptions")
            return
        
        # Créer l'API CJ
        cj_api = CJDropshippingApiOptimized(
            email=os.getenv('CJ_EMAIL'),
            password=os.getenv('CJ_PASSWORD')
        )
        
        enriched = 0
        failed = 0
        
        for i, product in enumerate(products_without_desc, 1):
            print(f"\n[{i}/{total}] {product.name[:60]}...")
            
            if enrich_product_details(product, cj_api):
                enriched += 1
            else:
                failed += 1
            
            # Délai pour éviter le rate limit (2 secondes entre chaque)
            if i < total:
                time.sleep(2)
        
        print("\n" + "="*70)
        print("RÉSUMÉ")
        print("="*70)
        print(f"Total traités: {total}")
        print(f"✅ Enrichis: {enriched}")
        print(f"❌ Échecs: {failed}")
        print(f"Taux de succès: {round(enriched/total*100, 1)}%")
        print("="*70 + "\n")

if __name__ == '__main__':
    main()
