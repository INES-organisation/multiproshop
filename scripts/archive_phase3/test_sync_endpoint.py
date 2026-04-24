"""
Test direct de l'endpoint de synchronisation
"""
import requests
import json

def test_sync_endpoint():
    """Tester l'endpoint de synchronisation directement"""
    
    print("="*80)
    print("TEST DE L'ENDPOINT DE SYNCHRONISATION")
    print("="*80)
    
    # URL de l'endpoint
    url = "http://127.0.0.1:5000/admin/api/providers/1/sync"
    
    print(f"\nURL: {url}")
    print("Méthode: POST")
    
    try:
        # Faire la requête POST
        response = requests.post(
            url,
            headers={'Content-Type': 'application/json'},
            timeout=300  # 5 minutes max
        )
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        # Afficher le contenu brut
        print(f"\n--- Contenu brut ---")
        print(response.text[:1000])
        
        # Essayer de parser en JSON
        try:
            data = response.json()
            print(f"\n--- JSON parsé ---")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            if data.get('success'):
                print(f"\n✅ Synchronisation réussie!")
                print(f"   Créés: {data.get('created', 0)}")
                print(f"   Mis à jour: {data.get('updated', 0)}")
                print(f"   Échecs: {data.get('failed', 0)}")
            else:
                print(f"\n✗ Échec de synchronisation")
                print(f"   Message: {data.get('message', 'N/A')}")
                
        except json.JSONDecodeError as e:
            print(f"\n✗ Erreur de parsing JSON: {e}")
            print(f"   Position: {e.pos}")
            print(f"   Ligne: {e.lineno}")
            
    except requests.exceptions.RequestException as e:
        print(f"\n✗ Erreur de requête: {e}")
    except Exception as e:
        print(f"\n✗ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_sync_endpoint()
