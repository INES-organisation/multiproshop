"""
Script de debug pour diagnostiquer les problèmes de synchronisation CJ
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from app import app
from services.api_providers.cj_dropshipping_optimized import CJDropshippingApiOptimized
from config import Config
import time

def test_api_connection():
    """Tester la connexion à l'API CJ"""
    print("\n" + "="*70)
    print("DEBUG SYNCHRONISATION CJ")
    print("="*70 + "\n")
    
    with app.app_context():
        try:
            # Initialiser l'API
            print("1. Initialisation API CJ...")
            print(f"   Email: {Config.CJ_EMAIL}")
            print(f"   Base URL: {Config.CJ_BASE_URL}")
            
            cj_api = CJDropshippingApiOptimized(
                email=Config.CJ_EMAIL,
                password=Config.CJ_PASSWORD,
                dev_key=Config.CJ_DEV_KEY
            )
            print("   ✓ API initialisée\n")
            
            # Test 1: Obtenir token
            print("2. Test authentification...")
            token = cj_api.get_access_token()
            
            if token:
                print(f"   ✓ Token obtenu: {token[:20]}...")
            else:
                print("   ✗ Échec obtention token")
                print("   Vérifier les logs ci-dessus pour l'erreur")
                return False
            
            # Attendre un peu pour éviter rate limit
            print("\n3. Attente 2 secondes...\n")
            time.sleep(2)
            
            # Test 2: Récupérer catégories
            print("4. Test récupération catégories...")
            categories = cj_api.get_categories()
            
            if categories:
                print(f"   ✓ {len(categories)} catégories récupérées")
                
                # Afficher quelques exemples
                print("\n   Exemples de catégories:")
                for i, cat in enumerate(categories[:3]):
                    print(f"   - {cat.get('categoryName')} (ID: {cat.get('categoryId')})")
                
                return True
            else:
                print("   ✗ Aucune catégorie récupérée")
                return False
            
        except Exception as e:
            print(f"\n✗ ERREUR: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    success = test_api_connection()
    
    print("\n" + "="*70)
    if success:
        print("✓ API CJ FONCTIONNELLE")
        print("\nVous pouvez maintenant synchroniser via l'interface web:")
        print("http://multiproshop.local/admin/cj/categories")
    else:
        print("✗ PROBLÈME DÉTECTÉ")
        print("\nVérifier:")
        print("1. Identifiants CJ dans .env")
        print("2. Connexion internet")
        print("3. Rate limit CJ (attendre 5 minutes)")
    print("="*70 + "\n")
