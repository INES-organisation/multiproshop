"""
Forcer la synchronisation des catégories CJ avec logs détaillés
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from app import create_app
from services.api_providers.cj_dropshipping_optimized import CJDropshippingApiOptimized
from services.cj_sync_service import CjSyncService
from config import Config
import logging

# Configurer logging détaillé
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

app = create_app()

with app.app_context():
    print("\n" + "="*70)
    print("SYNCHRONISATION FORCÉE CATÉGORIES CJ")
    print("="*70 + "\n")
    
    print("1. Création API CJ...")
    cj_api = CJDropshippingApiOptimized(
        email=Config.CJ_EMAIL,
        password=Config.CJ_PASSWORD,
        dev_key=Config.CJ_DEV_KEY
    )
    print(f"   Email: {cj_api.email}")
    print("   [OK]\n")
    
    print("2. Création service de synchronisation...")
    sync_service = CjSyncService(cj_api)
    print("   [OK]\n")
    
    print("3. Lancement synchronisation...")
    print("   (Cela peut prendre 1-2 minutes)\n")
    
    result = sync_service.sync_categories()
    
    print("\n" + "="*70)
    print("RÉSULTAT")
    print("="*70)
    
    if result['success']:
        print(f"✓ Succès: {result['synced']}/{result['total']} catégories synchronisées")
        if result.get('errors'):
            print(f"\n⚠️  {len(result['errors'])} erreurs:")
            for err in result['errors'][:10]:
                print(f"  - {err['category']}: {err['error'][:100]}...")
    else:
        print(f"✗ Échec: {result['message']}")
        if result.get('errors'):
            print(f"\nErreurs ({len(result['errors'])}):")
            for err in result['errors'][:10]:
                print(f"  - {err['category']}: {err['error'][:100]}...")
    
    print("="*70 + "\n")
