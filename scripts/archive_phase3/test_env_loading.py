"""
Test du chargement des variables d'environnement
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

print("\n" + "="*70)
print("TEST CHARGEMENT .ENV")
print("="*70 + "\n")

# Test 1: Charger .env
print("1. Chargement .env...")
load_dotenv(override=True)
print("   [OK] load_dotenv() execute\n")

# Test 2: Vérifier variables
print("2. Variables CJ:")
cj_email = os.getenv('CJ_EMAIL')
cj_password = os.getenv('CJ_PASSWORD')
cj_dev_key = os.getenv('CJ_DEV_KEY')

print(f"   CJ_EMAIL: {cj_email}")
print(f"   CJ_PASSWORD: {'*' * len(cj_password) if cj_password else 'VIDE'}")
print(f"   CJ_DEV_KEY: {'*' * len(cj_dev_key) if cj_dev_key else 'VIDE'}")

# Test 3: Vérifier Config
print("\n3. Test Config class:")
from config import Config

print(f"   Config.CJ_EMAIL: {Config.CJ_EMAIL}")
print(f"   Config.CJ_PASSWORD: {'*' * len(Config.CJ_PASSWORD) if Config.CJ_PASSWORD else 'VIDE'}")
print(f"   Config.CJ_DEV_KEY: {'*' * len(Config.CJ_DEV_KEY) if Config.CJ_DEV_KEY else 'VIDE'}")

# Test 4: Test API
print("\n4. Test API CJ:")
if Config.CJ_EMAIL:
    from services.api_providers.cj_dropshipping_optimized import CJDropshippingApiOptimized
    
    api = CJDropshippingApiOptimized(
        email=Config.CJ_EMAIL,
        password=Config.CJ_PASSWORD,
        dev_key=Config.CJ_DEV_KEY
    )
    
    print(f"   API email: {api.email}")
    print("   [OK] API initialisee")
else:
    print("   [ERREUR] CJ_EMAIL vide - .env non charge")

print("\n" + "="*70)
if Config.CJ_EMAIL:
    print("[OK] Variables CJ chargees correctement")
else:
    print("[ERREUR] Variables CJ non chargees")
    print("\nSolution:")
    print("1. Verifier que .env existe")
    print("2. Verifier le contenu de .env")
    print("3. Redemarrer le serveur")
print("="*70 + "\n")
