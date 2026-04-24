"""
Script de diagnostic pour la synchronisation CJ
"""
import requests
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'instance', 'multiproshop.db')

def get_cj_credentials():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, api_key, api_secret, api_endpoint FROM api_provider WHERE slug = 'cj-dropshipping'")
    result = cursor.fetchone()
    conn.close()
    return result

def get_access_token(api_key, api_secret, endpoint):
    api_key_formatted = f"{api_key}@api@{api_secret}"
    url = f"{endpoint}/authentication/getAccessToken"
    
    try:
        response = requests.post(url, json={"apiKey": api_key_formatted}, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 200:
                return data.get('data', {}).get('accessToken')
    except Exception as e:
        print(f"Erreur token: {e}")
    return None

def get_mappings():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT external_category_id, external_category_name, mps_category_id
        FROM category_mapping
        WHERE provider_id = 1 AND auto_import = 1
        LIMIT 10
    """)
    results = cursor.fetchall()
    conn.close()
    return results

def test_category_products(access_token, endpoint, category_id, category_name):
    url = f"{endpoint}/product/list"
    headers = {'CJ-Access-Token': access_token}
    params = {'pageNum': 1, 'pageSize': 10, 'categoryId': category_id}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('code') == 200:
                products = data.get('data', {}).get('list', [])
                return len(products), None
            else:
                return 0, f"Code API: {data.get('code')} - {data.get('message')}"
        else:
            return 0, f"HTTP {response.status_code}"
    except Exception as e:
        return 0, str(e)

def main():
    print("="*80)
    print("DIAGNOSTIC DE SYNCHRONISATION CJ DROPSHIPPING")
    print("="*80)
    
    # 1. Credentials
    print("\n1. Récupération des identifiants...")
    creds = get_cj_credentials()
    if not creds:
        print("✗ Provider non trouvé")
        return
    
    provider_id, api_key, api_secret, endpoint = creds
    print(f"✓ Provider ID: {provider_id}")
    
    # 2. Access token
    print("\n2. Obtention de l'access token...")
    access_token = get_access_token(api_key, api_secret, endpoint)
    if not access_token:
        print("✗ Impossible d'obtenir le token")
        return
    print("✓ Token obtenu")
    
    # 3. Mappings
    print("\n3. Récupération des mappings...")
    mappings = get_mappings()
    print(f"✓ {len(mappings)} mappings trouvés")
    
    # 4. Test de chaque catégorie
    print("\n4. Test des catégories:")
    print("-" * 80)
    
    total_products = 0
    categories_with_products = 0
    
    for cat_id, cat_name, mps_id in mappings:
        count, error = test_category_products(access_token, endpoint, cat_id, cat_name)
        
        if error:
            print(f"✗ {cat_name[:40]:<40} | Erreur: {error}")
        elif count > 0:
            print(f"✓ {cat_name[:40]:<40} | {count} produits")
            total_products += count
            categories_with_products += 1
        else:
            print(f"○ {cat_name[:40]:<40} | 0 produits")
    
    # 5. Résumé
    print("\n" + "="*80)
    print("RÉSUMÉ")
    print("="*80)
    print(f"Catégories testées: {len(mappings)}")
    print(f"Catégories avec produits: {categories_with_products}")
    print(f"Total produits trouvés: {total_products}")
    
    if total_products == 0:
        print("\n⚠️  PROBLÈME: Aucun produit trouvé dans les catégories testées")
        print("   Causes possibles:")
        print("   - Les catégories CJ sont vides")
        print("   - Rate limit API atteint")
        print("   - Problème de filtrage par catégorie")
    else:
        print(f"\n✅ {total_products} produits disponibles pour import")

if __name__ == '__main__':
    main()
