"""
Test simple de récupération des catégories CJ Dropshipping
"""
import requests
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

def get_access_token(api_key, api_secret, endpoint):
    """Obtenir un access token CJ"""
    api_key_formatted = f"{api_key}@api@{api_secret}"
    
    url = f"{endpoint}/authentication/getAccessToken"
    
    try:
        response = requests.post(
            url,
            json={"apiKey": api_key_formatted},
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 200:
                return data.get('data', {}).get('accessToken')
        
        print(f"Erreur obtention token: {response.text}")
        return None
    except Exception as e:
        print(f"Erreur: {e}")
        return None

def test_categories():
    """Tester la récupération des catégories CJ"""
    
    print("="*70)
    print("TEST DE RÉCUPÉRATION DES CATÉGORIES CJ DROPSHIPPING")
    print("="*70)
    
    credentials = get_cj_credentials()
    
    if not credentials:
        print("✗ Impossible de récupérer les identifiants")
        return False
    
    api_key, api_secret, endpoint = credentials
    
    print(f"\nAPI Key: {api_key}")
    print(f"Endpoint: {endpoint}")
    
    # Utiliser le token existant (valide jusqu'en 2026-01-02)
    print("\n1. Utilisation du token existant...")
    access_token = "API@CJ3088897@CJ:eyJhbGciOiJIUzI1NiJ9.eyJqdGkiOiIyMTkwNCIsInR5cGUiOiJBQ0NFU1NfVE9LRU4iLCJzdWIiOiJicUxvYnFRMGxtTm55UXB4UFdMWnloY2taSEFNdURGVFJKSWdyWTlkOHNTbTVvSnJaWjVmSExjUUd1Ykp6YzJGTndYb1F5UWhZdlVaVUhFWmlXMDZUT2NSdEIvL2Rwc2JoMWlhaEw1b3R5Z05aUHNrODF4TVlaRm9LTG9GblF5WGxBcDBLL21tNDByUU9EQnZONUc2VzZaV045dlZGZURGakpWSHltQVY2VVVoSHkrcG9pa0RFQ2VzVEVyYjZiaEhSeXhOT01oOEhVWnVmbXUwUGU2YXFXZDVDZ UJhdGdkUXd6b0RJZW8wN1diRUs5Mkpoc3lmajBVcnNmVkJHMG5vQkhWWkZZVDBZOGJ1MEsydlFZdzZkQ0lSaUJ2VU5IQWZ5enYvWDFGUTNibmRDbCtER3RmNjNXSUFTOHVrK2M2eiIsImlhdCI6MTc2NjAzOTY0OX0.ud0ud4Xzz3VhOrorDovtktvWZHneC8FnTlNV25xQAJ0"
    
    print(f"✓ Token valide jusqu'au 2026-01-02")
    
    # Récupérer les catégories
    print("\n2. Récupération des catégories...")
    
    url = f"{endpoint}/product/getCategory"
    headers = {
        'CJ-Access-Token': access_token,
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Code API: {data.get('code')}")
            print(f"Message: {data.get('message')}")
            
            if data.get('code') == 200:
                raw_data = data.get('data', [])
                
                if not raw_data:
                    print("✗ Aucune catégorie retournée par l'API")
                    return False
                
                # Parser la structure hiérarchique
                categories = []
                for first_level in raw_data:
                    first_name = first_level.get('categoryFirstName', '')
                    
                    for second_level in first_level.get('categoryFirstList', []):
                        second_name = second_level.get('categorySecondName', '')
                        
                        for category in second_level.get('categorySecondList', []):
                            categories.append({
                                'id': category.get('categoryId'),
                                'name': category.get('categoryName'),
                                'path': f"{first_name} > {second_name} > {category.get('categoryName')}"
                            })
                
                print(f"\n✓ {len(categories)} catégories récupérées")
                
                # Afficher les premières catégories
                print("\n3. Détails des catégories:")
                print("-" * 70)
                
                for i, cat in enumerate(categories[:10], 1):
                    print(f"\n{i}. {cat.get('name', 'N/A')}")
                    print(f"   ID: {cat.get('id', 'N/A')}")
                    print(f"   Path: {cat.get('path', 'N/A')}")
                
                if len(categories) > 10:
                    print(f"\n... et {len(categories) - 10} autres catégories")
                
                print("\n" + "="*70)
                print("RÉSUMÉ")
                print("="*70)
                print(f"✓ API CJ Dropshipping opérationnelle")
                print(f"✓ {len(categories)} catégories disponibles")
                print("\nLe problème de mapping peut venir de:")
                print("1. L'interface web qui ne charge pas les catégories")
                print("2. Un problème de session/authentification dans Flask")
                print("3. Une erreur JavaScript dans le template")
                
                return True
            else:
                print(f"✗ Erreur API: {data.get('message')}")
                return False
        else:
            print(f"✗ Erreur HTTP: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"✗ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_categories()
    exit(0 if success else 1)
