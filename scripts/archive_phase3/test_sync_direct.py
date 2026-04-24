"""
Test direct de la fonction de synchronisation pour identifier l'erreur
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configuration Flask minimale
os.environ['FLASK_ENV'] = 'development'

from app import create_app
from models.api_provider import ApiProvider, CategoryMapping
from services.api_providers.cj_dropshipping_optimized import CJDropshippingProvider

def test_sync():
    """Tester la synchronisation directement"""
    print("="*80)
    print("TEST DIRECT DE SYNCHRONISATION")
    print("="*80)
    
    app = create_app('development')
    
    with app.app_context():
        # Récupérer le provider
        provider = ApiProvider.query.filter_by(slug='cj-dropshipping').first()
        
        if not provider:
            print("✗ Provider non trouvé")
            return
        
        print(f"\n1. Provider: {provider.name}")
        
        # Créer le service
        try:
            service = CJDropshippingProvider(provider)
            print("✓ Service CJ créé")
        except Exception as e:
            print(f"✗ Erreur création service: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # Récupérer les mappings
        print("\n2. Récupération des mappings...")
        priority_categories = ['Scarves & Wraps', 'Hats & Caps', 'Gloves & Mittens']
        
        all_mappings = CategoryMapping.query.filter_by(
            provider_id=provider.id,
            auto_import=True
        ).all()
        
        print(f"   Total mappings: {len(all_mappings)}")
        
        # Trier
        priority_mappings = [m for m in all_mappings if m.external_category_name in priority_categories]
        other_mappings = [m for m in all_mappings if m.external_category_name not in priority_categories]
        
        mappings = (priority_mappings + other_mappings)[:10]
        
        print(f"   Mappings prioritaires: {len(priority_mappings)}")
        print(f"   Mappings sélectionnés: {len(mappings)}")
        
        # Tester la récupération de produits
        print("\n3. Test de récupération de produits...")
        
        for idx, mapping in enumerate(mappings[:3], 1):  # Tester seulement 3 catégories
            print(f"\n   {idx}. {mapping.external_category_name}")
            print(f"      ID externe: {mapping.external_category_id}")
            
            try:
                result = service.get_products(
                    category_id=mapping.external_category_id,
                    limit=10
                )
                
                products = result.get('products', [])
                print(f"      ✓ {len(products)} produits récupérés")
                
                if products:
                    p = products[0]
                    print(f"      Premier produit:")
                    print(f"        - Nom: {p.get('name', 'N/A')[:50]}")
                    print(f"        - ID: {p.get('external_id', 'N/A')}")
                    print(f"        - Prix: ${p.get('price', 0)}")
                    
            except Exception as e:
                print(f"      ✗ Erreur: {e}")
                import traceback
                traceback.print_exc()
        
        print("\n" + "="*80)
        print("FIN DU TEST")
        print("="*80)

if __name__ == '__main__':
    test_sync()
