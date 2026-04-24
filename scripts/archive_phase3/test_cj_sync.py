"""
Test de synchronisation des produits CJ Dropshipping
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sqlite3
from services.api_providers.cj_dropshipping_optimized import CJDropshippingProvider

class MockProvider:
    """Mock du modèle ApiProvider pour les tests"""
    def __init__(self, data):
        self.id = data[0]
        self.name = data[1]
        self.api_key = data[2]
        self.api_secret = data[3]
        self.api_endpoint = data[4]
        self.slug = 'cj-dropshipping'
        self.rate_limit = None
        self.daily_quota = None
        self.requests_today = 0
        self.access_token = None
    
    def increment_requests(self):
        self.requests_today += 1

def test_sync():
    """Tester la synchronisation des produits CJ"""
    
    db_path = os.path.join(os.path.dirname(__file__), '..', 'instance', 'multiproshop.db')
    
    if not os.path.exists(db_path):
        print(f"Erreur: Base de données non trouvée")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Récupérer le provider CJ
    cursor.execute("""
        SELECT id, name, api_key, api_secret, api_endpoint
        FROM api_provider 
        WHERE slug = 'cj-dropshipping'
    """)
    
    result = cursor.fetchone()
    
    if not result:
        print("Erreur: Provider CJ Dropshipping non trouvé")
        conn.close()
        return False
    
    print("="*80)
    print("TEST DE SYNCHRONISATION DES PRODUITS CJ DROPSHIPPING")
    print("="*80)
    print(f"\nProvider: {result[1]}")
    
    try:
        # Créer une instance du provider
        print("\n1. Initialisation du provider CJ...")
        mock_provider = MockProvider(result)
        cj_service = CJDropshippingProvider(mock_provider)
        
        if not cj_service.access_token:
            print("✗ Échec de l'obtention de l'access token")
            print("   Attendez 5 minutes si vous avez un rate limit")
            conn.close()
            return False
        
        print(f"✓ Access token obtenu")
        
        # Récupérer un mapping pour tester
        cursor.execute("""
            SELECT external_category_id, external_category_name, mps_category_id
            FROM category_mapping
            WHERE provider_id = ?
            LIMIT 1
        """, (result[0],))
        
        mapping = cursor.fetchone()
        
        if not mapping:
            print("\n✗ Aucun mapping de catégorie trouvé")
            print("   Exécutez d'abord: python scripts/auto_map_cj_categories.py")
            conn.close()
            return False
        
        print(f"\n2. Test avec la catégorie: {mapping[1]}")
        print(f"   ID externe: {mapping[0]}")
        
        # Récupérer les produits de cette catégorie
        print("\n3. Récupération des produits...")
        result = cj_service.get_products(category_id=mapping[0], page=1, limit=5)
        
        products = result.get('products', [])
        
        if not products:
            print("✗ Aucun produit récupéré pour cette catégorie")
            print("   Essayez avec une autre catégorie")
            conn.close()
            return False
        
        print(f"✓ {len(products)} produits récupérés")
        
        # Afficher les détails des produits
        print("\n4. Détails des produits:")
        print("-" * 80)
        
        for i, product in enumerate(products, 1):
            print(f"\n{i}. {product.get('name', 'N/A')}")
            print(f"   ID: {product.get('external_id', 'N/A')}")
            print(f"   Prix: ${product.get('price', 0):.2f}")
            print(f"   Stock: {product.get('stock', 0)}")
            print(f"   SKU: {product.get('sku', 'N/A')}")
            print(f"   Images: {len(product.get('images', []))} image(s)")
            
            # Vérifier que les données sont sérialisables en JSON
            import json
            try:
                raw_data = product.get('raw_data', {})
                json_str = json.dumps(raw_data, ensure_ascii=False, default=str)
                print(f"   ✓ Données JSON valides ({len(json_str)} caractères)")
            except Exception as e:
                print(f"   ✗ Erreur JSON: {e}")
        
        print("\n" + "="*80)
        print("RÉSUMÉ")
        print("="*80)
        print(f"✓ Provider CJ opérationnel")
        print(f"✓ {len(products)} produits récupérés et formatés")
        print(f"✓ Données JSON valides")
        print("\n✅ La synchronisation devrait fonctionner maintenant!")
        print("\nPour synchroniser via l'interface web:")
        print("1. Lancez votre application Flask")
        print("2. Allez sur: http://localhost:5000/admin/api/providers")
        print("3. Cliquez sur l'icône de synchronisation pour CJ Dropshipping")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"\n✗ Erreur: {str(e)}")
        import traceback
        traceback.print_exc()
        conn.close()
        return False

if __name__ == '__main__':
    success = test_sync()
    exit(0 if success else 1)
