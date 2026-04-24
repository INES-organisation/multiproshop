"""
Test de synchronisation des produits CJ
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

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

app = create_app()

with app.app_context():
    print("\n" + "="*70)
    print("TEST SYNCHRONISATION PRODUITS CJ")
    print("="*70 + "\n")
    
    # Récupérer une catégorie CJ pour tester
    print("1. Recherche d'une catégorie CJ pour test...")
    category = Category.query.filter(
        Category.cj_category_id.isnot(None),
        Category.level == 3
    ).first()
    
    if not category:
        print("   ✗ Aucune catégorie CJ trouvée")
        print("   Synchronise d'abord les catégories !")
        sys.exit(1)
    
    print(f"   ✓ Catégorie trouvée: {category.name}")
    print(f"   CJ ID: {category.cj_category_id}")
    print(f"   Niveau: {category.level}\n")
    
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
    
    print(f"4. Test sync_products() pour catégorie '{category.name}'...")
    print(f"   (Limite: 10 produits pour test rapide)\n")
    
    result = sync_service.sync_products(
        category_id=category.cj_category_id,
        limit=10
    )
    
    print("\n" + "="*70)
    print("RÉSULTAT")
    print("="*70)
    
    if result['success']:
        print(f"✓ Succès: {result['synced']} produits synchronisés")
        print(f"  Total disponible: {result.get('total', 'N/A')}")
        
        if result.get('errors'):
            print(f"\n⚠️  {len(result['errors'])} erreurs:")
            for err in result['errors'][:5]:
                print(f"  - {err.get('product', 'N/A')}: {err.get('error', 'N/A')[:80]}...")
    else:
        print(f"✗ Échec: {result['message']}")
        
        if result.get('errors'):
            print(f"\nErreurs ({len(result['errors'])}):")
            for err in result['errors'][:5]:
                print(f"  - {err.get('product', 'N/A')}: {err.get('error', 'N/A')[:80]}...")
    
    print("="*70 + "\n")
