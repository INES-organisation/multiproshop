"""
Script de re-synchronisation complète des produits CJ avec TOUTES les données
Sauvegarde les données brutes (cj_raw_data) pour chaque produit
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
import json
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

app = create_app()

def resync_product_full_data(product, cj_api):
    """Re-synchroniser un produit avec toutes les données complètes"""
    try:
        logger.info(f"[{product.id}] {product.name[:50]}...")
        
        # Récupérer les détails complets du produit
        product_details = cj_api.get_product_details(product.cj_pid)
        
        if not product_details:
            logger.warning(f"  ⚠️  Pas de détails retournés pour {product.cj_pid}")
            return False
        
        # Sauvegarder les données brutes COMPLÈTES
        product.cj_raw_data = json.dumps(product_details, ensure_ascii=False)
        
        # Extraire et mettre à jour toutes les informations disponibles
        
        # Description
        description = (
            product_details.get('description') or 
            product_details.get('productDesc') or 
            product_details.get('productDescEn') or
            product_details.get('productDescription')
        )
        if description:
            product.description = description
            logger.info(f"  ✓ Description: {len(description)} chars")
        else:
            logger.warning(f"  ⚠️  Pas de description disponible")
        
        # Spécifications
        specs = product_details.get('specifications') or product_details.get('productSpec')
        if specs:
            product.specifications = json.dumps(specs, ensure_ascii=False)
            logger.info(f"  ✓ Spécifications ajoutées")
        
        # Images supplémentaires
        images = product_details.get('productImage') or product_details.get('images') or []
        if isinstance(images, str):
            images = [images]
        
        if images:
            # Image principale
            if not product.image_url and images:
                product.image_url = images[0]
                logger.info(f"  ✓ Image principale ajoutée")
            
            # Images supplémentaires
            if len(images) > 1:
                product.set_images_list(images[1:])
                logger.info(f"  ✓ {len(images)-1} images supplémentaires")
        
        # Dimensions et poids
        if product_details.get('productWeight'):
            product.product_weight = str(product_details.get('productWeight'))
        
        if product_details.get('packLength'):
            product.length = float(product_details.get('packLength', 0))
        if product_details.get('packWidth'):
            product.width = float(product_details.get('packWidth', 0))
        if product_details.get('packHeight'):
            product.height = float(product_details.get('packHeight', 0))
        
        # Matériau
        if product_details.get('material'):
            product.material = product_details.get('material')
        
        # Marque
        if product_details.get('brand'):
            product.brand = product_details.get('brand')
        
        # Mettre à jour la date de dernière sync
        from datetime import datetime
        product.cj_last_sync = datetime.utcnow()
        
        db.session.commit()
        logger.info(f"  ✅ Produit re-synchronisé avec succès")
        return True
        
    except Exception as e:
        logger.error(f"  ❌ Erreur: {e}")
        db.session.rollback()
        return False

def main():
    with app.app_context():
        print("\n" + "="*70)
        print("RE-SYNCHRONISATION COMPLÈTE DES PRODUITS CJ")
        print("Sauvegarde de TOUTES les données brutes pour usage futur")
        print("="*70 + "\n")
        
        # Récupérer tous les produits CJ
        products = Product.query.filter(
            Product.cj_pid.isnot(None),
            Product.published == True
        ).all()
        
        total = len(products)
        print(f"Produits à re-synchroniser: {total}\n")
        
        if total == 0:
            print("❌ Aucun produit CJ trouvé")
            return
        
        # Créer l'API CJ
        cj_api = CJDropshippingApiOptimized(
            email=os.getenv('CJ_EMAIL'),
            password=os.getenv('CJ_PASSWORD')
        )
        
        print("⏳ Attente de 5 minutes pour éviter le rate limit CJ...")
        print("   (Le rate limit expire à chaque fois après 5 minutes)\n")
        
        # Attendre 5 minutes
        for remaining in range(300, 0, -30):
            mins = remaining // 60
            secs = remaining % 60
            print(f"   Temps restant: {mins}m {secs:02d}s", end='\r')
            time.sleep(30)
        
        print("\n\n✓ Attente terminée, début de la synchronisation...\n")
        
        synced = 0
        failed = 0
        no_data = 0
        
        for i, product in enumerate(products, 1):
            print(f"\n[{i}/{total}] ", end='')
            
            result = resync_product_full_data(product, cj_api)
            
            if result:
                synced += 1
            else:
                # Vérifier si c'est un manque de données ou une erreur
                if product.cj_raw_data:
                    failed += 1
                else:
                    no_data += 1
            
            # Délai progressif pour éviter le rate limit
            if i < total:
                if i % 10 == 0:
                    delay = 5  # 5 secondes toutes les 10 requêtes
                else:
                    delay = 2  # 2 secondes entre chaque
                
                time.sleep(delay)
            
            # Afficher la progression tous les 50 produits
            if i % 50 == 0:
                print(f"\n{'='*70}")
                print(f"PROGRESSION: {i}/{total} ({round(i/total*100, 1)}%)")
                print(f"Synchronisés: {synced} | Échecs: {failed} | Sans données: {no_data}")
                print(f"{'='*70}\n")
        
        print("\n" + "="*70)
        print("RÉSUMÉ FINAL")
        print("="*70)
        print(f"Total traités: {total}")
        print(f"✅ Synchronisés avec succès: {synced}")
        print(f"⚠️  Sans données disponibles: {no_data}")
        print(f"❌ Échecs: {failed}")
        print(f"Taux de succès: {round(synced/total*100, 1)}%")
        print("="*70 + "\n")
        
        # Vérifier les descriptions
        with_desc = Product.query.filter(
            Product.cj_pid.isnot(None),
            Product.published == True,
            Product.description.isnot(None),
            Product.description != ''
        ).count()
        
        print(f"📝 Produits avec description: {with_desc}/{total} ({round(with_desc/total*100, 1)}%)")
        
        # Vérifier les raw_data
        with_raw = Product.query.filter(
            Product.cj_pid.isnot(None),
            Product.published == True,
            Product.cj_raw_data.isnot(None)
        ).count()
        
        print(f"💾 Produits avec données brutes: {with_raw}/{total} ({round(with_raw/total*100, 1)}%)")
        print()

if __name__ == '__main__':
    main()
