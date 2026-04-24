"""
Script de test pour synchroniser les catégories CJ
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from services.cj_sync_service import CjSyncService
from services.api_providers.cj_dropshipping_optimized import CJDropshippingApiOptimized
from config import Config

def test_sync_categories():
    """Tester la synchronisation des catégories"""
    print("\n" + "="*70)
    print("TEST SYNCHRONISATION CATEGORIES CJ")
    print("="*70 + "\n")
    
    with app.app_context():
        try:
            # Créer l'API CJ
            print("1. Initialisation API CJ...")
            cj_api = CJDropshippingApiOptimized(
                email=Config.CJ_EMAIL,
                password=Config.CJ_PASSWORD,
                dev_key=Config.CJ_DEV_KEY
            )
            print("   ✓ API initialisée")
            
            # Créer le service de sync
            print("\n2. Création du service de synchronisation...")
            sync_service = CjSyncService(cj_api)
            print("   ✓ Service créé")
            
            # Synchroniser les catégories
            print("\n3. Synchronisation des catégories...")
            print("   (Cela peut prendre quelques secondes...)")
            result = sync_service.sync_categories()
            
            print("\n" + "="*70)
            print("RÉSULTAT")
            print("="*70)
            
            if result['success']:
                print(f"✓ Succès !")
                print(f"  - Total catégories CJ : {result['total']}")
                print(f"  - Catégories synchronisées : {result['synced']}")
                print(f"  - Nouvelles catégories : {result.get('new', 0)}")
                print(f"  - Catégories mises à jour : {result.get('updated', 0)}")
            else:
                print(f"✗ Échec : {result.get('message', 'Erreur inconnue')}")
            
            print("\n" + "="*70)
            
        except Exception as e:
            print(f"\n✗ ERREUR : {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    test_sync_categories()
