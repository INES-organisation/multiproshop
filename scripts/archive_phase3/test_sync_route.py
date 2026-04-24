"""
Test direct de la route de synchronisation
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from app import create_app
import traceback

print("\n" + "="*70)
print("TEST ROUTE SYNCHRONISATION")
print("="*70 + "\n")

app = create_app()

with app.app_context():
    try:
        print("1. Import des modules...")
        from services.api_providers.cj_dropshipping_optimized import CJDropshippingApiOptimized
        from services.cj_sync_service import CjSyncService
        from config import Config
        print("   [OK] Imports reussis\n")
        
        print("2. Verification Config...")
        print(f"   CJ_EMAIL: {Config.CJ_EMAIL}")
        print(f"   CJ_PASSWORD: {'*' * len(Config.CJ_PASSWORD) if Config.CJ_PASSWORD else 'VIDE'}")
        print(f"   CJ_DEV_KEY: {'*' * len(Config.CJ_DEV_KEY) if Config.CJ_DEV_KEY else 'VIDE'}")
        print()
        
        print("3. Creation API CJ...")
        cj_api = CJDropshippingApiOptimized(
            email=Config.CJ_EMAIL,
            password=Config.CJ_PASSWORD,
            dev_key=Config.CJ_DEV_KEY
        )
        print(f"   API email: {cj_api.email}")
        print("   [OK] API creee\n")
        
        print("4. Creation CjSyncService...")
        sync_service = CjSyncService(cj_api)
        print("   [OK] Service cree\n")
        
        print("5. Test sync_categories()...")
        result = sync_service.sync_categories()
        print(f"   Resultat: {result}\n")
        
        if result.get('success'):
            print("="*70)
            print("[OK] SYNCHRONISATION REUSSIE")
            print(f"Categories synchronisees: {result.get('count', 0)}")
            print("="*70)
        else:
            print("="*70)
            print("[ERREUR] SYNCHRONISATION ECHOUEE")
            print(f"Message: {result.get('message', 'Inconnu')}")
            print("="*70)
            
    except Exception as e:
        print("="*70)
        print("[ERREUR EXCEPTION]")
        print(f"Type: {type(e).__name__}")
        print(f"Message: {str(e)}")
        print("\nTraceback complet:")
        traceback.print_exc()
        print("="*70)
