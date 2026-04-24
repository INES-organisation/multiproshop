"""
Test rapide de synchronisation avec UNE seule catégorie
"""
import requests
import sqlite3
import os
import time

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'instance', 'multiproshop.db')

def main():
    print("="*80)
    print("TEST RAPIDE DE SYNCHRONISATION")
    print("="*80)
    
    # Récupérer les credentials
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT api_key, api_secret, api_endpoint FROM api_provider WHERE slug = 'cj-dropshipping'")
    api_key, api_secret, endpoint = cursor.fetchone()
    
    # Obtenir un token
    print("\n1. Obtention du token...")
    api_key_formatted = f"{api_key}@api@{api_secret}"
    response = requests.post(
        f"{endpoint}/authentication/getAccessToken",
        json={"apiKey": api_key_formatted},
        timeout=10
    )
    
    if response.status_code != 200:
        print(f"✗ Erreur: {response.status_code}")
        print(f"   {response.text}")
        return
    
    data = response.json()
    if data.get('code') != 200:
        print(f"✗ Code API: {data.get('code')} - {data.get('message')}")
        return
    
    access_token = data.get('data', {}).get('accessToken')
    print("✓ Token obtenu")
    
    # Tester avec une catégorie qui a des produits
    print("\n2. Test avec la catégorie 'Scarves & Wraps'...")
    cursor.execute("""
        SELECT external_category_id, external_category_name
        FROM category_mapping
        WHERE provider_id = 1 AND external_category_name = 'Scarves & Wraps'
    """)
    
    result = cursor.fetchone()
    if not result:
        print("✗ Catégorie non trouvée")
        conn.close()
        return
    
    category_id, category_name = result
    print(f"   ID: {category_id}")
    
    # Récupérer les produits
    print("\n3. Récupération des produits...")
    response = requests.get(
        f"{endpoint}/product/list",
        headers={'CJ-Access-Token': access_token},
        params={'pageNum': 1, 'pageSize': 10, 'categoryId': category_id},
        timeout=30
    )
    
    if response.status_code != 200:
        print(f"✗ HTTP {response.status_code}")
        conn.close()
        return
    
    data = response.json()
    
    if data.get('code') != 200:
        print(f"✗ Code API: {data.get('code')} - {data.get('message')}")
        conn.close()
        return
    
    products = data.get('data', {}).get('list', [])
    print(f"✓ {len(products)} produits trouvés")
    
    if products:
        print("\n4. Premier produit:")
        p = products[0]
        print(f"   Nom: {p.get('productName', 'N/A')}")
        print(f"   ID: {p.get('pid', 'N/A')}")
        print(f"   Prix: ${p.get('sellPrice', 0)}")
        print(f"   Stock: {p.get('stock', 0)}")
        
        print("\n✅ Les produits sont disponibles!")
        print("\nProblème possible:")
        print("- Le rate limit empêche la synchronisation complète")
        print("- Les autres catégories sont vides")
        print("\nSolution:")
        print("1. Attendez 5 minutes entre chaque synchronisation")
        print("2. Ou désactivez auto_import pour les catégories vides")
    else:
        print("\n⚠️  Cette catégorie est vide")
    
    conn.close()

if __name__ == '__main__':
    main()
