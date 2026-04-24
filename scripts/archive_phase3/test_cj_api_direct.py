"""
Test direct de l'API CJ pour diagnostiquer le problème
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import requests
import json
from config import Config

def test_cj_api_direct():
    """Tester l'API CJ directement sans passer par notre classe"""
    print("\n" + "="*70)
    print("TEST DIRECT API CJ")
    print("="*70 + "\n")
    
    # Étape 1: Authentification
    print("1. Authentification...")
    auth_url = "https://developers.cjdropshipping.com/api2.0/v1/authentication/getAccessToken"
    
    auth_data = {
        'email': Config.CJ_EMAIL,
        'password': Config.CJ_PASSWORD
    }
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    if Config.CJ_DEV_KEY:
        headers['CJ-DEV-KEY'] = Config.CJ_DEV_KEY
    
    print(f"   Email: {Config.CJ_EMAIL}")
    print(f"   URL: {auth_url}")
    
    try:
        response = requests.post(auth_url, json=auth_data, headers=headers, verify=False, timeout=30)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('result') and 'data' in data:
                token = data['data'].get('accessToken')
                print(f"   [OK] Token obtenu: {token[:30]}...")
                
                # Étape 2: Récupérer catégories
                print("\n2. Récupération catégories...")
                cat_url = "https://developers.cjdropshipping.com/api2.0/v1/product/getCategory"
                
                cat_headers = {
                    'Content-Type': 'application/json',
                    'CJ-Access-Token': token
                }
                
                if Config.CJ_DEV_KEY:
                    cat_headers['CJ-DEV-KEY'] = Config.CJ_DEV_KEY
                
                cat_response = requests.get(cat_url, headers=cat_headers, verify=False, timeout=30)
                print(f"   Status: {cat_response.status_code}")
                
                if cat_response.status_code == 200:
                    cat_data = cat_response.json()
                    
                    print(f"\n   Réponse brute (premiers 500 caractères):")
                    print(f"   {str(cat_data)[:500]}...")
                    
                    if cat_data.get('result'):
                        categories = cat_data.get('data', [])
                        print(f"\n   [OK] {len(categories)} categories niveau 1 recuperees")
                        
                        if categories:
                            # Compter total
                            total = 0
                            for first in categories:
                                total += 1
                                for second in first.get('categoryFirstList', []):
                                    total += 1
                                    for third in second.get('categorySecondList', []):
                                        total += 1
                            
                            print(f"   [OK] Total categories (tous niveaux): {total}")
                            
                            # Afficher exemple
                            print(f"\n   Exemple categorie niveau 1:")
                            first = categories[0]
                            print(f"   - ID: {first.get('categoryFirstId')}")
                            print(f"   - Nom: {first.get('categoryFirstName')}")
                            print(f"   - Sous-categories: {len(first.get('categoryFirstList', []))}")
                            
                            return True
                        else:
                            print("   [ERREUR] Aucune categorie dans data")
                            return False
                    else:
                        print(f"   [ERREUR] Erreur API: {cat_data.get('message')}")
                        return False
                else:
                    print(f"   [ERREUR] Erreur HTTP: {cat_response.status_code}")
                    print(f"   Réponse: {cat_response.text[:200]}")
                    return False
            else:
                print(f"   [ERREUR] Erreur auth: {data.get('message')}")
                return False
        else:
            print(f"   [ERREUR] Erreur HTTP: {response.status_code}")
            print(f"   Réponse: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"   [ERREUR] Exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print(f"\nConfiguration:")
    print(f"  CJ_EMAIL: {Config.CJ_EMAIL}")
    print(f"  CJ_PASSWORD: {'*' * len(Config.CJ_PASSWORD) if Config.CJ_PASSWORD else 'VIDE'}")
    print(f"  CJ_DEV_KEY: {'*' * len(Config.CJ_DEV_KEY) if Config.CJ_DEV_KEY else 'VIDE'}")
    
    success = test_cj_api_direct()
    
    print("\n" + "="*70)
    if success:
        print("[OK] API CJ FONCTIONNELLE - Les categories sont accessibles")
        print("\nLe problème vient probablement de notre code de synchronisation.")
    else:
        print("[ERREUR] PROBLEME API CJ")
        print("\nVérifier:")
        print("1. Identifiants CJ corrects dans .env")
        print("2. Rate limit (attendre 5 minutes)")
        print("3. Connexion internet")
    print("="*70 + "\n")
