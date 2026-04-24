import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from extensions import db
from models.api_provider import ApiProvider, CategoryMapping
from models.product import Product
from services.api_providers.cj_dropshipping_optimized import CJDropshippingProvider
from routes.api_management import create_product_from_source

with app.app_context():
    provider = ApiProvider.query.filter_by(slug='cj-dropshipping').first()
    service = CJDropshippingProvider(provider)
    
    # Prendre 1 seule catégorie
    mapping = CategoryMapping.query.filter_by(
        provider_id=provider.id,
        auto_import=True
    ).first()
    
    print(f"\nTest synchronisation rapide")
    print(f"Categorie: {mapping.external_category_name}")
    print(f"Categorie MPS: {mapping.mps_category.name}\n")
    
    # Récupérer 3 produits
    result = service.get_products(category_id=mapping.external_category_id, limit=3)
    
    created = 0
    for product_data in result.get('products', []):
        try:
            create_product_from_source(provider, product_data, mapping)
            db.session.commit()
            created += 1
            print(f"✓ Produit cree: {product_data.get('name')}")
        except Exception as e:
            db.session.rollback()
            print(f"✗ Erreur: {e}")
    
    print(f"\n{created} produits crees avec succes")
    
    # Afficher les produits
    products = Product.query.limit(5).all()
    print(f"\nProduits dans la base:")
    for p in products:
        print(f"  - {p.name} ({p.category.name}) - {p.price}€ - Stock: {p.stock}")
        print(f"    Image: {p.image_url}")
