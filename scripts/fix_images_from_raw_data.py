"""
Script pour corriger l'extraction des images depuis cj_raw_data
Les images sont stockées comme string JSON au lieu de liste
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.product import Product
from extensions import db
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

app = create_app()

def fix_product_images(product):
    """Corriger les images d'un produit depuis cj_raw_data"""
    try:
        if not product.cj_raw_data:
            return False
        
        raw_data = json.loads(product.cj_raw_data)
        
        # Récupérer le champ images
        images_field = raw_data.get('images', [])
        
        # Si c'est une liste avec une string JSON dedans
        if isinstance(images_field, list) and len(images_field) > 0:
            if isinstance(images_field[0], str) and images_field[0].startswith('['):
                # C'est une string JSON, il faut la parser
                try:
                    images_list = json.loads(images_field[0])
                    
                    # Mettre à jour l'image principale si nécessaire
                    if images_list and not product.image_url:
                        product.image_url = images_list[0]
                    
                    # Mettre à jour les images supplémentaires
                    if len(images_list) > 1:
                        product.set_images_list(images_list[1:])
                        logger.info(f"  ✓ {len(images_list)-1} images supplémentaires ajoutées")
                        return True
                except json.JSONDecodeError:
                    logger.warning(f"  ⚠️  Impossible de parser les images JSON")
                    return False
        
        # Si c'est déjà une liste normale
        elif isinstance(images_field, list) and len(images_field) > 1:
            if not product.image_url:
                product.image_url = images_field[0]
            product.set_images_list(images_field[1:])
            logger.info(f"  ✓ {len(images_field)-1} images supplémentaires ajoutées")
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"  ❌ Erreur: {e}")
        return False

def main():
    with app.app_context():
        print("\n" + "="*70)
        print("CORRECTION DES IMAGES DEPUIS cj_raw_data")
        print("="*70 + "\n")
        
        # Récupérer tous les produits avec raw_data
        products = Product.query.filter(
            Product.cj_pid.isnot(None),
            Product.cj_raw_data.isnot(None)
        ).all()
        
        total = len(products)
        print(f"Produits à traiter: {total}\n")
        
        if total == 0:
            print("❌ Aucun produit avec cj_raw_data")
            return
        
        fixed = 0
        no_images = 0
        
        for i, product in enumerate(products, 1):
            if i % 100 == 0:
                print(f"Progression: {i}/{total}...")
            
            if fix_product_images(product):
                fixed += 1
            else:
                no_images += 1
        
        # Sauvegarder
        if fixed > 0:
            db.session.commit()
            print(f"\n✅ {fixed} produits mis à jour avec images supplémentaires")
        
        print("\n" + "="*70)
        print("RÉSUMÉ")
        print("="*70)
        print(f"Total traités: {total}")
        print(f"✅ Avec images supplémentaires: {fixed}")
        print(f"⚠️  Sans images supplémentaires: {no_images}")
        print(f"Taux de succès: {round(fixed/total*100, 1)}%")
        print("="*70 + "\n")
        
        # Vérifier un produit
        test_product = Product.query.filter(
            Product.cj_pid.isnot(None),
            Product.cj_raw_data.isnot(None)
        ).first()
        
        if test_product:
            imgs = test_product.get_images_list()
            print(f"Test - Produit: {test_product.name[:50]}")
            print(f"Images supplémentaires: {len(imgs)}")
            if imgs:
                print(f"Première image: {imgs[0][:80]}...")

if __name__ == '__main__':
    main()
