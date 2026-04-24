"""
Tester la connexion au provider CJ Dropshipping
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
    
    def increment_requests(self):
        self.requests_today += 1

def test_cj_connection():
    """Tester la connexion CJ"""
    
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
    
    print(f"Test de connexion pour: {result[1]}")
    print(f"Email: {result[2]}")
    print(f"Endpoint: {result[4]}")
    print("\nConnexion en cours...")
    
    # Créer une instance du provider
    mock_provider = MockProvider(result)
    cj_service = CJDropshippingProvider(mock_provider)
    
    # Tester la connexion
    try:
        is_connected = cj_service.test_connection()
        
        if is_connected:
            print("\n✓ Connexion réussie!")
            print("\nTest de récupération des catégories...")
            
            categories = cj_service.get_categories()
            print(f"✓ {len(categories)} catégories récupérées")
            
            if categories:
                print("\nPremières catégories:")
                for cat in categories[:5]:
                    print(f"  - {cat.get('name')} (ID: {cat.get('id')})")
            
            return True
        else:
            print("\n✗ Échec de la connexion")
            print("Vérifiez vos identifiants CJ Dropshipping")
            return False
            
    except Exception as e:
        print(f"\n✗ Erreur lors du test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_cj_connection()
    exit(0 if success else 1)
