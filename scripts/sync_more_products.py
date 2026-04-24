import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models.api_provider import ApiProvider, CategoryMapping, ApiSyncLog, ProductSource
from models.product import Product
from services.api_providers.cj_dropshipping_optimized import CJDropshippingProvider
from datetime import datetime
import time

def get_provider_service(provider):
    if provider.slug == 'cj-dropshipping':
        return CJDropshippingProvider(provider)
    raise Exception(f"Provider {provider.slug} non supporté")

def create_product_from_source(provider, product_data, mapping):
    import re
    
    price = float(product_data.get('price', 0)) * mapping.apply_markup
    compare_price = float(product_data.get('compare_price', 0)) * mapping.apply_markup
    
    images = product_data.get('images', [])
    image_url = images[0] if images and len(images) > 0 else None
    
    product_name = product_data.get('name', 'Produit sans nom')
    if isinstance(product_name, list):
        product_name = product_name[0] if product_name else 'Produit sans nom'
    
    sku = product_data.get('sku', '')
    external_id = str(product_data.get('external_id', ''))
    
    if sku:
        base_slug = sku.lower().replace('_', '-')
    else:
        base_slug = f"product-{external_id}"
    
    slug = re.sub(r'[^a-z0-9-]', '', base_slug)
    
    counter = 1
    original_slug = slug
    while Product.query.filter_by(slug=slug).first():
        slug = f"{original_slug}-{counter}"
        counter += 1
    
    product = Product(
        name=product_data.get('name', 'Produit sans nom'),
        slug=slug,
        description=product_data.get('description', ''),
        price=price,
        compare_price=compare_price,
        stock=int(product_data.get('stock', 0)),
        sku=product_data.get('sku', f"{provider.slug}-{product_data.get('external_id', 'unknown')}"),
        category_id=mapping.mps_category_id,
        image_url=image_url,
        is_active=True
    )
    
    db.session.add(product)
    db.session.flush()
    
    source = ProductSource(
        product_id=product.id,
        provider_id=provider.id,
        external_product_id=str(product_data.get('external_id', '')),
        external_price=float(product_data.get('price', 0)),
        external_stock=int(product_data.get('stock', 0)),
        external_currency=product_data.get('currency', 'USD'),
        sync_status='synced',
        last_synced_at=datetime.utcnow()
    )
    
    raw_data = product_data.get('raw_data', {})
    if raw_data:
        source.set_raw_data(raw_data)
    
    db.session.add(source)
    return product

with app.app_context():
    print("\n" + "="*80)
    print("SYNCHRONISATION MASSIVE DE PRODUITS CJ DROPSHIPPING")
    print("="*80 + "\n")
    
    provider = ApiProvider.query.filter_by(slug='cj-dropshipping').first()
    if not provider:
        print("❌ Provider CJ Dropshipping non trouvé")
        exit(1)
    
    service = get_provider_service(provider)
    
    # Récupérer tous les mappings actifs
    all_mappings = CategoryMapping.query.filter_by(
        provider_id=provider.id,
        auto_import=True
    ).all()
    
    print(f"📊 Mappings actifs trouvés: {len(all_mappings)}")
    
    # Synchroniser 20 catégories avec 10 produits chacune = 200 produits
    mappings = all_mappings[:20]
    
    total_created = 0
    total_failed = 0
    
    for idx, mapping in enumerate(mappings, 1):
        print(f"\n[{idx}/{len(mappings)}] Catégorie: {mapping.external_category_name}")
        
        try:
            result = service.get_products(category_id=mapping.external_category_id, limit=10)
            products = result.get('products', [])
            print(f"  → {len(products)} produits trouvés")
            
            for product_data in products:
                try:
                    # Vérifier si existe déjà
                    source = ProductSource.query.filter_by(
                        provider_id=provider.id,
                        external_product_id=product_data['external_id']
                    ).first()
                    
                    if not source:
                        create_product_from_source(provider, product_data, mapping)
                        db.session.commit()
                        total_created += 1
                        print(f"    ✓ {product_data.get('name', 'N/A')[:50]}")
                    
                except Exception as e:
                    print(f"    ✗ Erreur: {e}")
                    db.session.rollback()
                    total_failed += 1
            
            # Pause pour éviter rate limit
            time.sleep(1)
            
        except Exception as e:
            print(f"  ✗ Erreur catégorie: {e}")
    
    print("\n" + "="*80)
    print(f"✓ Synchronisation terminée:")
    print(f"  - Produits créés: {total_created}")
    print(f"  - Échecs: {total_failed}")
    print(f"  - Total en base: {Product.query.count()}")
    print("="*80 + "\n")
