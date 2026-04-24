import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models.api_provider import ApiProvider, CategoryMapping
from services.api_providers.cj_dropshipping_optimized import CJDropshippingProvider
import json

with app.app_context():
    provider = ApiProvider.query.filter_by(slug='cj-dropshipping').first()
    
    if not provider:
        print("Provider CJ non trouve")
        exit(1)
    
    service = CJDropshippingProvider(provider)
    
    # Récupérer un mapping actif
    mapping = CategoryMapping.query.filter_by(
        provider_id=provider.id,
        auto_import=True
    ).first()
    
    if not mapping:
        print("Aucun mapping actif trouve")
        exit(1)
    
    print(f"\nTest avec categorie: {mapping.external_category_name}")
    print(f"ID categorie: {mapping.external_category_id}\n")
    
    # Récupérer 1 produit
    result = service.get_products(category_id=mapping.external_category_id, limit=1)
    
    if result.get('products'):
        product = result['products'][0]
        raw = product.get('raw_data', {})
        
        print("="*80)
        print("STRUCTURE COMPLETE DES DONNEES BRUTES CJ")
        print("="*80)
        print(json.dumps(raw, indent=2, ensure_ascii=False))
        
        print("\n" + "="*80)
        print("CHAMPS DISPONIBLES:")
        print("="*80)
        for key in sorted(raw.keys()):
            value = raw[key]
            if isinstance(value, (str, int, float)):
                print(f"  {key:30} = {value}")
            elif isinstance(value, list):
                print(f"  {key:30} = [liste de {len(value)} elements]")
            elif isinstance(value, dict):
                print(f"  {key:30} = {{dictionnaire}}")
    else:
        print("Aucun produit trouve")
