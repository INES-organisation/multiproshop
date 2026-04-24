"""
Script pour extraire les descriptions depuis les données brutes (cj_raw_data) déjà stockées
Plus rapide et évite le rate limit de l'API CJ
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

def extract_description_from_raw(product):
    """Extraire la description depuis cj_raw_data"""
    if not product.cj_raw_data:
        return None
    
    try:
        raw_data = json.loads(product.cj_raw_data)
        
        # Chercher la description dans différents champs possibles
        description = (
            raw_data.get('description') or 
            raw_data.get('productDesc') or 
            raw_data.get('productDescEn') or
            raw_data.get('productDescription') or
            raw_data.get('desc')
        )
        
        return description if description else None
        
    except Exception as e:
        logger.error(f"Erreur parsing JSON pour {product.id}: {e}")
        return None

def main():
    with app.app_context():
        print("\n" + "="*70)
        print("EXTRACTION DES DESCRIPTIONS DEPUIS LES DONNÉES BRUTES")
        print("="*70 + "\n")
        
        # Compter les produits avec raw_data
        products_with_raw = Product.query.filter(
            Product.cj_pid.isnot(None),
            Product.published == True,
            Product.cj_raw_data.isnot(None)
        ).all()
        
        total = len(products_with_raw)
        print(f"Produits avec données brutes: {total}\n")
        
        if total == 0:
            print("❌ Aucun produit avec données brutes")
            return
        
        # Analyser les données
        with_desc_in_raw = 0
        without_desc_in_raw = 0
        updated = 0
        
        for i, product in enumerate(products_with_raw, 1):
            if i % 100 == 0:
                print(f"Progression: {i}/{total} produits analysés...")
            
            # Extraire la description
            description = extract_description_from_raw(product)
            
            if description:
                with_desc_in_raw += 1
                
                # Mettre à jour si le produit n'a pas de description
                if not product.description:
                    product.description = description
                    updated += 1
            else:
                without_desc_in_raw += 1
        
        # Sauvegarder
        if updated > 0:
            db.session.commit()
            print(f"\n✅ {updated} descriptions mises à jour")
        
        print("\n" + "="*70)
        print("RÉSUMÉ")
        print("="*70)
        print(f"Total analysés: {total}")
        print(f"Avec description dans raw_data: {with_desc_in_raw}")
        print(f"Sans description dans raw_data: {without_desc_in_raw}")
        print(f"Descriptions ajoutées: {updated}")
        print(f"Taux de disponibilité: {round(with_desc_in_raw/total*100, 1)}%")
        print("="*70 + "\n")

if __name__ == '__main__':
    main()
