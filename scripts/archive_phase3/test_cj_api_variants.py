"""
Script pour tester si l'API CJ renvoie des variantes
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from services.cj_sync_service import CjSyncService
from services.api_providers.cj_dropshipping_optimized import CJDropshippingApiOptimized
from models.product import Product

def test_cj_api_variants():
    with app.app_context():
        print("\n" + "="*70)
        print("TEST API CJ - RÉCUPÉRATION VARIANTES")
        print("="*70 + "\n")
        
        cj_api = CJDropshippingApiOptimized()
        sync_service = CjSyncService(cj_api)
        
        # Prendre un produit CJ existant
        product = Product.query.filter(Product.cj_pid.isnot(None)).first()
        
        if not product:
            print("⚠️  Aucun produit CJ trouvé")
            return
        
        print(f"Test avec produit: {product.name[:60]}")
        print(f"CJ PID: {product.cj_pid}\n")
        
        # Récupérer les détails depuis l'API
        print("Appel API CJ...")
        details = sync_service.cj_api.get_product_details(product.cj_pid)
        
        if not details:
            print("❌ Aucun détail reçu de l'API")
            return
        
        print("✓ Détails reçus\n")
        
        # Vérifier les variantes
        variants = details.get('variants', [])
        print(f"Nombre de variantes: {len(variants)}")
        
        if len(variants) == 0:
            print("\n⚠️  CE PRODUIT N'A PAS DE VARIANTES")
            print("   Testez avec un autre produit qui a des variantes\n")
            
            # Chercher un produit avec variantes
            print("Recherche d'un produit avec variantes...")
            products = Product.query.filter(Product.cj_pid.isnot(None)).limit(10).all()
            
            for p in products:
                details = sync_service.cj_api.get_product_details(p.cj_pid)
                if details and len(details.get('variants', [])) > 0:
                    print(f"\n✓ Produit avec variantes trouvé: {p.name[:60]}")
                    print(f"  CJ PID: {p.cj_pid}")
                    print(f"  Variantes: {len(details['variants'])}")
                    
                    # Afficher les variantes
                    for i, v in enumerate(details['variants'][:5], 1):
                        print(f"\n  Variante {i}:")
                        print(f"    VID: {v.get('vid')}")
                        print(f"    Key: {v.get('key')}")
                        print(f"    Prix: ${v.get('price')}")
                        print(f"    Stock: {v.get('stock')}")
                    
                    break
        else:
            print("\n✓ VARIANTES TROUVÉES:\n")
            for i, v in enumerate(variants[:5], 1):
                print(f"Variante {i}:")
                print(f"  VID: {v.get('vid')}")
                print(f"  Key: {v.get('key')}")
                print(f"  Prix: ${v.get('price')}")
                print(f"  Stock: {v.get('stock')}")
                print()

if __name__ == '__main__':
    test_cj_api_variants()
