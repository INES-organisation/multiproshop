"""
Synchronisation produits CJ avec retry automatique en cas de rate limit
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
from models.category import Category
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def wait_for_rate_limit():
    """Attendre 5 minutes si rate limit détecté"""
    print("\n⏳ Rate limit CJ détecté")
    print("   Attente de 5 minutes (300 secondes)...\n")
    
    for remaining in range(300, 0, -30):
        mins = remaining // 60
        secs = remaining % 60
        print(f"   Temps restant: {mins}m {secs}s", end='\r')
        time.sleep(30)
    
    print("\n✓ Attente terminée, nouvelle tentative...\n")

app = create_app()

with app.app_context():
    print("\n" + "="*70)
    print("SYNCHRONISATION PRODUITS CJ AVEC RETRY")
    print("="*70 + "\n")
    
    # Récupérer une catégorie CJ pour test
    print("1. Sélection d'une catégorie CJ...")
    category = Category.query.filter(
        Category.cj_category_id.isnot(None),
        Category.level == 3
    ).first()
    
    if not category:
        print("   ✗ Aucune catégorie CJ trouvée")
        print("   Synchronise d'abord les catégories !")
        sys.exit(1)
    
    print(f"   ✓ Catégorie: {category.name}")
    print(f"   CJ ID: {category.cj_category_id}\n")
    
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        print(f"Tentative {retry_count + 1}/{max_retries}\n")
        
        print("2. Création API CJ...")
        cj_api = CJDropshippingApiOptimized(
            email=Config.CJ_EMAIL,
            password=Config.CJ_PASSWORD,
            dev_key=Config.CJ_DEV_KEY
        )
        print(f"   Email: {cj_api.email}")
        print("   [OK]\n")
        
        print("3. Création service de synchronisation...")
        sync_service = CjSyncService(cj_api)
        print("   [OK]\n")
        
        print(f"4. Synchronisation produits (limite: 20)...")
        result = sync_service.sync_products(
            category_id=category.cj_category_id,
            limit=20
        )
        
        if result['success'] and result['synced'] > 0:
            print("\n" + "="*70)
            print("✓ SYNCHRONISATION RÉUSSIE")
            print("="*70)
            print(f"Produits synchronisés: {result['synced']}")
            
            if result.get('errors'):
                print(f"\n⚠️  {len(result['errors'])} erreurs:")
                for err in result['errors'][:5]:
                    print(f"  - {err['product']}: {err['error'][:80]}...")
            
            print("="*70 + "\n")
            break
        else:
            # Vérifier si c'est un rate limit
            if result['synced'] == 0:
                print("\n⚠️  Rate limit ou aucun produit")
                retry_count += 1
                
                if retry_count < max_retries:
                    wait_for_rate_limit()
                else:
                    print("\n" + "="*70)
                    print("✗ ÉCHEC APRÈS 3 TENTATIVES")
                    print("="*70)
                    print("Le rate limit CJ persiste.")
                    print("Attends 10-15 minutes puis réessaye via l'interface web.")
                    print("="*70 + "\n")
            else:
                print("\n" + "="*70)
                print("✗ ERREUR")
                print("="*70)
                print(f"Message: {result['message']}")
                print("="*70 + "\n")
                break
