"""Test rapide de l'API CJ après nettoyage du rate limit"""
from app import create_app
from services.api_providers.cj_dropshipping_optimized import CJDropshippingApiOptimized
from config import Config

app = create_app()

with app.app_context():
    print("="*70)
    print("TEST API CJ APRÈS NETTOYAGE RATE LIMIT")
    print("="*70)
    
    cj_api = CJDropshippingApiOptimized(
        email=Config.CJ_EMAIL,
        password=Config.CJ_PASSWORD,
        dev_key=Config.CJ_DEV_KEY
    )
    
    print("\nTest récupération produits (10 premiers):")
    result = cj_api.get_products(page=1, page_size=10)
    
    print(f"✓ Total produits disponibles: {result.get('total', 0)}")
    print(f"✓ Produits récupérés: {len(result.get('products', []))}")
    
    if result.get('products'):
        print(f"\n✓ API CJ FONCTIONNELLE !")
        print(f"  Premier produit: {result['products'][0].get('name', 'N/A')[:50]}")
        print(f"  PID: {result['products'][0].get('pid', 'N/A')}")
    else:
        print("\n✗ Aucun produit récupéré - rate limit peut-être encore actif")
    
    print("\n" + "="*70)
