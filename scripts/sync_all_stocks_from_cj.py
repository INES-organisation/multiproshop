"""
Script pour synchroniser tous les stocks (produits et variantes) depuis CJ API
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from models.product import Product
from models.product_variant import ProductVariant
from services.api_providers.cj_dropshipping_optimized import CJDropshippingApiOptimized
from services.cj_variant_sync_service import CjVariantSyncService
from extensions import db
from config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def sync_all_stocks():
    """Synchroniser tous les stocks depuis CJ"""
    
    with app.app_context():
        print("\n" + "="*80)
        print("SYNCHRONISATION COMPLÈTE DES STOCKS DEPUIS CJ API")
        print("="*80 + "\n")
        
        # Initialiser l'API CJ
        try:
            cj_api = CJDropshippingApiOptimized(
                email=Config.CJ_EMAIL,
                password=Config.CJ_PASSWORD,
                dev_key=Config.CJ_DEV_KEY
            )
            print("✓ API CJ initialisée\n")
        except Exception as e:
            print(f"❌ Erreur initialisation API CJ: {e}\n")
            return
        
        # Initialiser le service de sync variantes
        variant_sync_service = CjVariantSyncService(cj_api)
        
        # Récupérer tous les produits CJ
        products = Product.query.filter(
            Product.cj_pid.isnot(None),
            Product.is_active == True
        ).all()
        
        print(f"Produits CJ à synchroniser: {len(products)}\n")
        
        if len(products) == 0:
            print("❌ Aucun produit CJ trouvé\n")
            return
        
        # Statistiques
        stats = {
            'products_processed': 0,
            'products_updated': 0,
            'products_failed': 0,
            'variants_updated': 0,
            'variants_failed': 0
        }
        
        # Synchroniser chaque produit
        for i, product in enumerate(products, 1):
            print(f"\n[{i}/{len(products)}] Produit: {product.name[:50]}...")
            print(f"  CJ PID: {product.cj_pid}")
            
            try:
                # Récupérer les données du produit depuis CJ
                product_data = cj_api.get_product_details(product.cj_pid)
                
                if not product_data:
                    print(f"  ⚠️  Impossible de récupérer les données CJ")
                    stats['products_failed'] += 1
                    continue
                
                # Extraire le stock du produit principal
                stock = 0
                if isinstance(product_data, dict):
                    data = product_data.get('data', {})
                    stock = int(data.get('sellQuantity', 0) or data.get('quantity', 0) or 0)
                
                # Mettre à jour le stock du produit
                old_stock = product.stock
                product.stock = stock
                
                print(f"  Stock produit: {old_stock} → {stock}")
                stats['products_updated'] += 1
                
                # Synchroniser les variantes si elles existent
                variants = ProductVariant.query.filter_by(product_id=product.id).all()
                
                if variants:
                    print(f"  Variantes: {len(variants)}")
                    
                    # Utiliser le service de sync variantes
                    result = variant_sync_service.sync_all_variants_stock(product.id)
                    
                    if result['success']:
                        print(f"  ✓ Variantes mises à jour: {result['updated']}/{result['total']}")
                        stats['variants_updated'] += result['updated']
                    else:
                        print(f"  ⚠️  Erreur sync variantes: {result['message']}")
                        stats['variants_failed'] += len(variants)
                
                stats['products_processed'] += 1
                
                # Commit par lots de 10
                if i % 10 == 0:
                    db.session.commit()
                    print(f"\n  ✓ Lot {i//10} sauvegardé")
                
            except Exception as e:
                logger.error(f"Erreur produit {product.cj_pid}: {e}")
                print(f"  ❌ Erreur: {e}")
                stats['products_failed'] += 1
                continue
        
        # Commit final
        db.session.commit()
        
        # Afficher les statistiques
        print("\n" + "="*80)
        print("RÉSUMÉ DE LA SYNCHRONISATION")
        print("="*80)
        print(f"\nProduits:")
        print(f"  • Traités: {stats['products_processed']}")
        print(f"  • Mis à jour: {stats['products_updated']}")
        print(f"  • Échecs: {stats['products_failed']}")
        
        print(f"\nVariantes:")
        print(f"  • Mises à jour: {stats['variants_updated']}")
        print(f"  • Échecs: {stats['variants_failed']}")
        
        print("\n✅ Synchronisation terminée !\n")


if __name__ == '__main__':
    sync_all_stocks()
