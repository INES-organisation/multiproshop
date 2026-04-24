"""
Synchroniser des produits pour plusieurs catégories CJ
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
import time

app = create_app()

# Liste de catégories CJ à synchroniser (exemples)
CATEGORIES_TO_SYNC = [
    'D91A4505-6495-4DFD-9984-C8E728913127',  # Boy Accessories
    '2502190916291603600',  # Couple&Parent-Child Short-Sleeves
    '2502190916401605200',  # Couple&Parent-Child Jackets
]

with app.app_context():
    print("\n" + "="*70)
    print("SYNCHRONISATION MULTIPLE DE CATÉGORIES CJ")
    print("="*70 + "\n")
    
    cj_api = CJDropshippingApiOptimized(
        email=Config.CJ_EMAIL,
        password=Config.CJ_PASSWORD,
        dev_key=Config.CJ_DEV_KEY
    )
    
    sync_service = CjSyncService(cj_api)
    
    total_synced = 0
    
    for i, cj_cat_id in enumerate(CATEGORIES_TO_SYNC, 1):
        # Trouver la catégorie
        category = Category.query.filter_by(cj_category_id=cj_cat_id).first()
        
        if not category:
            print(f"{i}. Catégorie {cj_cat_id[:20]}... non trouvée - SKIP\n")
            continue
        
        print(f"{i}. Synchronisation: {category.name}")
        print(f"   CJ ID: {cj_cat_id}")
        
        # Synchroniser 50 produits max par catégorie
        result = sync_service.sync_products(
            category_id=cj_cat_id,
            limit=50
        )
        
        if result['success']:
            print(f"   ✓ {result['synced']} produits synchronisés")
            total_synced += result['synced']
            
            if result.get('errors'):
                print(f"   ⚠️  {len(result['errors'])} erreurs")
        else:
            print(f"   ✗ Échec: {result['message']}")
        
        print()
        
        # Attendre 2 secondes entre chaque catégorie pour éviter le rate limit
        if i < len(CATEGORIES_TO_SYNC):
            time.sleep(2)
    
    print("="*70)
    print(f"TOTAL: {total_synced} produits synchronisés")
    print("="*70 + "\n")
