import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models.api_provider import ApiProvider, CategoryMapping
from services.api_providers.cj_dropshipping_optimized import CJDropshippingProvider

with app.app_context():
    provider = ApiProvider.query.filter_by(slug='cj-dropshipping').first()
    service = CJDropshippingProvider(provider)
    
    mapping = CategoryMapping.query.filter_by(
        provider_id=provider.id,
        auto_import=True
    ).first()
    
    print(f"\nTest formatage produit CJ")
    print(f"Categorie: {mapping.external_category_name}\n")
    
    result = service.get_products(category_id=mapping.external_category_id, limit=3)
    
    if result.get('products'):
        for i, product in enumerate(result['products'][:3], 1):
            print(f"\n{'='*80}")
            print(f"PRODUIT {i}")
            print(f"{'='*80}")
            print(f"Nom (EN):     {product.get('name')}")
            print(f"SKU:          {product.get('sku')}")
            print(f"Prix:         {product.get('price')} {product.get('currency')}")
            print(f"Stock:        {product.get('stock')}")
            print(f"Images:       {len(product.get('images', []))} image(s)")
            if product.get('images'):
                print(f"  - {product['images'][0]}")
            print(f"Categorie:    {product.get('category_name')}")
            print(f"Description:  {product.get('description')[:100]}...")
    else:
        print("Aucun produit trouve")
