"""
Script pour synchroniser le stock d'un seul produit et ses variantes depuis CJ
Usage: python scripts/sync_single_product_stock.py <product_id>
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


def sync_product_stock(product_id):
    """Synchroniser le stock d'un produit et ses variantes"""
    
    with app.app_context():
        print("\n" + "="*80)
        print(f"SYNCHRONISATION STOCK PRODUIT ID: {product_id}")
        print("="*80 + "\n")
        
        # Récupérer le produit
        product = Product.query.get(product_id)
        
        if not product:
            print(f"❌ Produit {product_id} introuvable\n")
            return
        
        if not product.cj_pid:
            print(f"❌ Produit {product_id} n'est pas un produit CJ\n")
            return
        
        print(f"Produit: {product.name}")
        print(f"CJ PID: {product.cj_pid}")
        print(f"Stock actuel: {product.stock}\n")
        
        # Initialiser l'API CJ
        try:
            cj_api = CJDropshippingApiOptimized(
                email=Config.CJ_EMAIL,
                password=Config.CJ_PASSWORD,
                dev_key=Config.CJ_DEV_KEY
            )
        except Exception as e:
            print(f"❌ Erreur initialisation API CJ: {e}\n")
            return
        
        # Récupérer les données depuis CJ
        print("Récupération données CJ...")
        product_data = cj_api.get_product_details(product.cj_pid)
        
        if not product_data:
            print("❌ Impossible de récupérer les données CJ\n")
            return
        
        # Extraire le stock
        stock = 0
        if isinstance(product_data, dict):
            data = product_data.get('data', {})
            stock = int(data.get('sellQuantity', 0) or data.get('quantity', 0) or 0)
        
        # Mettre à jour le stock du produit
        old_stock = product.stock
        product.stock = stock
        
        print(f"✓ Stock produit mis à jour: {old_stock} → {stock}\n")
        
        # Synchroniser les variantes
        variants = ProductVariant.query.filter_by(product_id=product_id).all()
        
        if variants:
            print(f"Variantes trouvées: {len(variants)}")
            print("Synchronisation des variantes...\n")
            
            variant_sync_service = CjVariantSyncService(cj_api)
            result = variant_sync_service.sync_all_variants_stock(product_id)
            
            if result['success']:
                print(f"✓ Variantes mises à jour: {result['updated']}/{result['total']}\n")
                
                # Afficher le détail des variantes
                variants_updated = ProductVariant.query.filter_by(product_id=product_id).all()
                print("Détail des variantes:")
                for v in variants_updated:
                    display_name = f"{v.color or 'N/A'} - {v.size or 'N/A'}"
                    print(f"  • {display_name}: Stock = {v.stock}")
            else:
                print(f"⚠️  Erreur sync variantes: {result['message']}\n")
        else:
            print("Aucune variante pour ce produit\n")
        
        # Sauvegarder
        db.session.commit()
        
        print("="*80)
        print("✅ SYNCHRONISATION TERMINÉE")
        print("="*80 + "\n")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("\nUsage: python scripts/sync_single_product_stock.py <product_id>")
        print("Exemple: python scripts/sync_single_product_stock.py 778\n")
        sys.exit(1)
    
    try:
        product_id = int(sys.argv[1])
        sync_product_stock(product_id)
    except ValueError:
        print("\n❌ L'ID du produit doit être un nombre\n")
        sys.exit(1)
