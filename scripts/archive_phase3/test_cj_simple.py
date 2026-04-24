"""
Test simple de la connexion CJ Dropshipping sans dépendances Flask
"""
import requests
import hashlib
import time
import sqlite3
import os

def get_cj_credentials():
    """Récupérer les identifiants depuis la DB"""
    db_path = os.path.join(os.path.dirname(__file__), '..', 'instance', 'multiproshop.db')
    
    if not os.path.exists(db_path):
        return None
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT api_key, api_secret, api_endpoint
        FROM api_provider 
        WHERE slug = 'cj-dropshipping'
    """)
    
    result = cursor.fetchone()
    conn.close()
    
    return result

def get_auth_headers(email, api_key):
    """Générer les headers d'authentification CJ"""
    timestamp = str(int(time.time() * 1000))
    
    # Signature CJ: MD5(email + key + timestamp)
    signature_string = f"{email}{api_key}{timestamp}"
    signature = hashlib.md5(signature_string.encode()).hexdigest()
    
    return {
        'CJ-Access-Token': email,
        'CJ-Signature': signature,
        'CJ-Timestamp': timestamp,
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

def test_cj_connection():
    """Tester la connexion CJ"""
    
    credentials = get_cj_credentials()
    
    if not credentials:
        print("Erreur: Impossible de récupérer les identifiants")
        return False
    
    email, api_key, endpoint = credentials
    
    print("Configuration CJ Dropshipping:")
    print(f"  Email: {email}")
    print(f"  API Key: {api_key[:10]}...")
    print(f"  Endpoint: {endpoint}")
    print("\nTest de connexion...")
    
    try:
        # Préparer la requête
        url = f"{endpoint}/product/list"
        headers = get_auth_headers(email, api_key)
        params = {'pageNum': 1, 'pageSize': 1}
        
        print(f"\nRequête: GET {url}")
        print(f"Headers: CJ-Access-Token={email}")
        
        # Faire la requête
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        print(f"\nCode de réponse: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Réponse JSON: {data}")
            
            if data.get('code') == 200:
                print("\n✓ Connexion réussie!")
                print(f"Message: {data.get('message', 'OK')}")
                
                # Test des catégories
                print("\nTest de récupération des catégories...")
                cat_url = f"{endpoint}/product/category/list"
                cat_response = requests.get(cat_url, headers=get_auth_headers(email, api_key), timeout=10)
                
                if cat_response.status_code == 200:
                    cat_data = cat_response.json()
                    if cat_data.get('code') == 200:
                        categories = cat_data.get('data', [])
                        print(f"✓ {len(categories)} catégories récupérées")
                        
                        if categories:
                            print("\nPremières catégories:")
                            for cat in categories[:5]:
                                print(f"  - {cat.get('categoryName')} (ID: {cat.get('categoryId')})")
                
                return True
            else:
                print(f"\n✗ Erreur API CJ: Code {data.get('code')}")
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
