"""
Test simple de synchronisation des produits CJ Dropshipping
"""
import requests
import sqlite3
import os
import json

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'instance', 'multiproshop.db')

def get_cj_credentials():
    """Récupérer les identifiants CJ depuis la DB"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, api_key, api_secret, api_endpoint
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

def get_mapping():
    """Récupérer un mapping de test"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT cm.external_category_id, cm.external_category_name, cm.mps_category_id, ap.id
        FROM category_mapping cm
        JOIN api_provider ap ON cm.provider_id = ap.id
        WHERE ap.slug = 'cj-dropshipping'
        LIMIT 1
    """)
    
    result = cursor.fetchone()
    conn.close()
    
    return result

def get_products(access_token, endpoint, category_id):
    """Récupérer les produits d'une catégorie"""
    url = f"{endpoint}/product/list"
    headers = {
        'CJ-Access-Token': access_token,
        'Content-Type': 'application/json'
    }
    params = {
        'pageNum': 1,
        'pageSize': 10,
        'categoryId': category_id
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('code') == 200:
                return data.get('data', {}).get('list', [])
        
        print(f"Erreur API: {response.text[:500]}")
        return []
    except Exception as e:
        print(f"Erreur récupération produits: {e}")
        return []

def test_sync():
    """Tester la synchronisation"""
    
    print("="*80)
    print("TEST DE SYNCHRONISATION DES PRODUITS CJ DROPSHIPPING")
    print("="*80)
    
    # 1. Récupérer les identifiants
    print("\n1. Récupération des identifiants CJ...")
    cj_creds = get_cj_credentials()
    
    if not cj_creds:
        print("✗ Provider CJ Dropshipping non trouvé")
        return False
    
    provider_id, api_key, api_secret, endpoint = cj_creds
    print(f"✓ Provider ID: {provider_id}")
    
    # 2. Obtenir un access token
    print("\n2. Obtention de l'access token...")
    access_token = get_access_token(api_key, api_secret, endpoint)
    
    if not access_token:
        print("✗ Impossible d'obtenir l'access token")
        print("   Attendez 5 minutes si vous avez un rate limit")
        return False
    
    print("✓ Access token obtenu")
    
    # 3. Récupérer un mapping
    print("\n3. Récupération d'un mapping de test...")
    mapping = get_mapping()
    
    if not mapping:
        print("✗ Aucun mapping trouvé")
        print("   Exécutez: python scripts/auto_map_cj_categories.py")
        return False
    
    category_id, category_name, mps_cat_id, _ = mapping
    print(f"✓ Catégorie: {category_name}")
    print(f"   ID externe: {category_id}")
    print(f"   ID MPS: {mps_cat_id}")
    
    # 4. Récupérer les produits
    print("\n4. Récupération des produits...")
    products = get_products(access_token, endpoint, category_id)
    
    if not products:
        print("✗ Aucun produit récupéré")
        print("   Cette catégorie peut être vide, essayez une autre")
        return False
    
    print(f"✓ {len(products)} produits récupérés")
    
    # 5. Tester la sérialisation JSON
    print("\n5. Test de sérialisation JSON des produits:")
    print("-" * 80)
    
    for i, product in enumerate(products[:5], 1):
        print(f"\n{i}. {product.get('productName', 'N/A')}")
        print(f"   ID: {product.get('pid', 'N/A')}")
        print(f"   Prix: ${product.get('sellPrice', 0)}")
        print(f"   Stock: {product.get('stock', 0)}")
        
        # Test de sérialisation
        try:
            json_str = json.dumps(product, ensure_ascii=False, default=str)
            print(f"   ✓ JSON valide ({len(json_str)} caractères)")
        except Exception as e:
            print(f"   ✗ Erreur JSON: {e}")
            return False
    
    print("\n" + "="*80)
    print("RÉSUMÉ")
    print("="*80)
    print(f"✓ Authentification CJ réussie")
    print(f"✓ {len(products)} produits récupérés")
    print(f"✓ Sérialisation JSON validée")
    print("\n✅ La synchronisation devrait fonctionner maintenant!")
    print("\nPour synchroniser:")
    print("1. Redémarrez votre application Flask")
    print("2. Allez sur: http://localhost:5000/admin/api/providers")
    print("3. Cliquez sur l'icône de synchronisation (🔄) pour CJ Dropshipping")
    
    return True

if __name__ == '__main__':
    try:
        success = test_sync()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Erreur: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
