"""
Obtenir et sauvegarder un nouveau token CJ dans la base de données
"""
import requests
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'instance', 'multiproshop.db')

def main():
    print("="*80)
    print("OBTENTION ET SAUVEGARDE DU TOKEN CJ")
    print("="*80)
    
    # Récupérer les credentials
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, api_key, api_secret, api_endpoint FROM api_provider WHERE slug = 'cj-dropshipping'")
    provider_id, api_key, api_secret, endpoint = cursor.fetchone()
    
    print(f"\n1. Provider ID: {provider_id}")
    
    # Obtenir un nouveau token
    print("\n2. Obtention d'un nouveau token...")
    api_key_formatted = f"{api_key}@api@{api_secret}"
    
    try:
        response = requests.post(
            f"{endpoint}/authentication/getAccessToken",
            json={"apiKey": api_key_formatted},
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"✗ Erreur HTTP: {response.status_code}")
            print(f"   {response.text}")
            conn.close()
            return False
        
        data = response.json()
        
        if data.get('code') != 200:
            print(f"✗ Code API: {data.get('code')} - {data.get('message')}")
            conn.close()
            return False
        
        access_token = data.get('data', {}).get('accessToken')
        print(f"✓ Token obtenu: {access_token[:50]}...")
        
        # Sauvegarder en base de données
        print("\n3. Sauvegarde en base de données...")
        cursor.execute(
            "UPDATE api_provider SET access_token = ? WHERE id = ?",
            (access_token, provider_id)
        )
        conn.commit()
        print("✓ Token sauvegardé")
        
        conn.close()
        
        print("\n" + "="*80)
        print("✅ SUCCÈS - Token CJ sauvegardé")
        print("="*80)
        print("\nVous pouvez maintenant lancer la synchronisation via l'interface web")
        return True
        
    except Exception as e:
        print(f"\n✗ Erreur: {e}")
        import traceback
        traceback.print_exc()
        conn.close()
        return False

if __name__ == '__main__':
    import time
    print("\n⏱️  Attendez 5 minutes depuis votre dernière tentative...")
    print("   Appuyez sur Entrée quand vous êtes prêt...")
    input()
    
    success = main()
    exit(0 if success else 1)
