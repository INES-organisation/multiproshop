"""
Test de récupération des catégories CJ Dropshipping
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
        self.rate_limit = None
        self.daily_quota = None
        self.requests_today = 0
        self.access_token = None
    
    def increment_requests(self):
        self.requests_today += 1

def test_categories():
    """Tester la récupération des catégories CJ"""
    
    # Récupérer les données du provider depuis la DB
    db_path = os.path.join(os.path.dirname(__file__), '..', 'instance', 'multiproshop.db')
    
    if not os.path.exists(db_path):
        print(f"Erreur: Base de données non trouvée")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, name, api_key, api_secret, api_endpoint
        FROM api_provider 
        WHERE slug = 'cj-dropshipping'
    """)
    
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        print("Erreur: Provider CJ Dropshipping non trouvé")
        return False
    
    print("="*70)
    print("TEST DE RÉCUPÉRATION DES CATÉGORIES CJ DROPSHIPPING")
    print("="*70)
    print(f"\nProvider: {result[1]}")
    print(f"API Key: {result[2]}")
    print(f"Endpoint: {result[4]}")
    
    try:
        # Créer une instance du provider
        print("\n1. Initialisation du provider CJ...")
        mock_provider = MockProvider(result)
        cj_service = CJDropshippingProvider(mock_provider)
        
        if not cj_service.access_token:
            print("✗ Échec de l'obtention de l'access token")
            return False
        
        print(f"✓ Access token obtenu: {cj_service.access_token[:30]}...")
        
        # Récupérer les catégories
        print("\n2. Récupération des catégories...")
        categories = cj_service.get_categories()
        
        if not categories:
            print("✗ Aucune catégorie récupérée")
            print("\nVérification de l'endpoint...")
            
            # Test direct de l'endpoint
            import requests
            url = f"{result[4]}/product/category/list"
            headers = {'CJ-Access-Token': cj_service.access_token}
            
            print(f"URL: {url}")
            response = requests.get(url, headers=headers, timeout=10)
            print(f"Status: {response.status_code}")
            print(f"Réponse: {response.text[:500]}")
            
            return False
        
        print(f"✓ {len(categories)} catégories récupérées")
        
        # Afficher les premières catégories
        print("\n3. Détails des catégories:")
        print("-" * 70)
        for i, cat in enumerate(categories[:10], 1):
            print(f"\n{i}. {cat.get('name', 'N/A')}")
            print(f"   ID: {cat.get('id', 'N/A')}")
            print(f"   Parent ID: {cat.get('parent_id', 'N/A')}")
            print(f"   Level: {cat.get('level', 'N/A')}")
            print(f"   Path: {cat.get('path', 'N/A')}")
        
        if len(categories) > 10:
            print(f"\n... et {len(categories) - 10} autres catégories")
        
        print("\n" + "="*70)
        print("RÉSUMÉ")
        print("="*70)
        print(f"✓ Provider CJ Dropshipping opérationnel")
        print(f"✓ {len(categories)} catégories disponibles pour le mapping")
        print("\nLe mapping des catégories devrait fonctionner maintenant.")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Erreur: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_categories()
    exit(0 if success else 1)
