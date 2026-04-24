"""
Test final de la connexion CJ Dropshipping avec le nouveau code
"""
import requests
import sqlite3
import os

def test_cj_connection():
    """Tester la connexion CJ avec le nouveau système d'authentification"""
    
    # Récupérer les identifiants
    db_path = os.path.join(os.path.dirname(__file__), '..', 'instance', 'multiproshop.db')
    
    if not os.path.exists(db_path):
        print("Erreur: Base de données non trouvée")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT api_key, api_secret, api_endpoint
        FROM api_provider 
        WHERE slug = 'cj-dropshipping'
    """)
    
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        print("Erreur: Provider CJ Dropshipping non trouvé")
        return False
    
    email, api_key, endpoint = result
    
    print("Configuration CJ Dropshipping:")
    print(f"  Email: {email}")
    print(f"  API Key: {api_key[:10]}...")
    print(f"  Endpoint: {endpoint}")
    print("\n" + "="*60)
    print("ÉTAPE 1: Obtention de l'access token")
    print("="*60)
    
    # Format de l'API Key CJ: email@api@apikey
    api_key_formatted = f"{email}@api@{api_key}"
    
    url = f"{endpoint}/authentication/getAccessToken"
    
    try:
        print(f"\nRequête POST: {url}")
        print(f"Payload: {{'apiKey': '{email}@api@{api_key[:10]}...'}}")
        
        response = requests.post(
            url,
            json={"apiKey": api_key_formatted},
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f"\nCode de réponse: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Réponse: {data}")
            
            if data.get('code') == 200:
                token_data = data.get('data', {})
                access_token = token_data.get('accessToken')
                
                print("\n✓ Access token obtenu avec succès!")
                print(f"  Access Token: {access_token[:20]}...")
                print(f"  Expiration: {token_data.get('accessTokenExpiryDate')}")
                
                print("\n" + "="*60)
                print("ÉTAPE 2: Test de l'API avec l'access token")
                print("="*60)
                
                # Tester l'API avec le token
                test_url = f"{endpoint}/product/list"
                headers = {
                    'CJ-Access-Token': access_token,
                    'Content-Type': 'application/json'
                }
                params = {'pageNum': 1, 'pageSize': 10}
                
                print(f"\nRequête GET: {test_url}")
                print(f"Headers: CJ-Access-Token={access_token[:20]}...")
                
                test_response = requests.get(test_url, headers=headers, params=params, timeout=10)
                
                print(f"\nCode de réponse: {test_response.status_code}")
                
                if test_response.status_code == 200:
                    test_data = test_response.json()
                    
                    if test_data.get('code') == 200:
                        print("\n✓ Connexion à l'API réussie!")
                        print(f"Message: {test_data.get('message')}")
                        
                        print("\n" + "="*60)
                        print("RÉSUMÉ")
                        print("="*60)
                        print("✓ Authentification réussie")
                        print("✓ Access token valide")
                        print("✓ API CJ Dropshipping fonctionnelle")
                        print("\nVous pouvez maintenant utiliser le provider CJ Dropshipping!")
                        return True
                    else:
                        print(f"\n✗ Erreur API: Code {test_data.get('code')}")
                        print(f"Message: {test_data.get('message')}")
                        return False
                else:
                    print(f"\n✗ Erreur HTTP: {test_response.status_code}")
                    print(f"Réponse: {test_response.text[:500]}")
                    return False
            else:
                print(f"\n✗ Erreur lors de l'obtention du token: Code {data.get('code')}")
                print(f"Message: {data.get('message')}")
                return False
        else:
            print(f"\n✗ Erreur HTTP: {response.status_code}")
            print(f"Réponse: {response.text[:500]}")
            return False
            
    except requests.exceptions.Timeout:
        print("\n✗ Timeout: La requête a pris trop de temps")
        return False
    except requests.exceptions.RequestException as e:
        print(f"\n✗ Erreur de connexion: {str(e)}")
        return False
    except Exception as e:
        print(f"\n✗ Erreur: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_cj_connection()
    exit(0 if success else 1)
