import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models.api_provider import ApiProvider, ProductSource
from models.product import Product

with app.app_context():
    print("\n" + "="*80)
    print("ANALYSE DES PRODUITS ET SOURCES")
    print("="*80 + "\n")
    
    total_products = Product.query.count()
    total_sources = ProductSource.query.count()
    
    print(f"Total Product (produits réels): {total_products}")
    print(f"Total ProductSource (liens d'import): {total_sources}")
    print()
    
    # Vérifier les ProductSource orphelins (sans Product associé)
    orphan_sources = ProductSource.query.filter(
        ~ProductSource.product_id.in_(db.session.query(Product.id))
    ).count()
    
    print(f"ProductSource orphelins (sans Product): {orphan_sources}")
    print()
    
    # Vérifier les doublons
    from sqlalchemy import func
    duplicates = db.session.query(
        ProductSource.external_product_id,
        func.count(ProductSource.id).label('count')
    ).group_by(
        ProductSource.external_product_id
    ).having(
        func.count(ProductSource.id) > 1
    ).all()
    
    print(f"Produits importés plusieurs fois: {len(duplicates)}")
    if duplicates:
        print("Exemples:")
        for ext_id, count in duplicates[:5]:
            print(f"  - External ID {ext_id}: {count} fois")
    print()
    
    print("="*80)
    print("CONCLUSION:")
    print("="*80)
    print()
    
    if orphan_sources > 0:
        print(f"⚠️  Il y a {orphan_sources} ProductSource orphelins à nettoyer")
    
    if len(duplicates) > 0:
        print(f"⚠️  Il y a {len(duplicates)} produits importés en double")
    
    print(f"\n✓ Le compteur correct devrait être: {total_products} (nombre de Product)")
    print(f"✗ Le compteur actuel affiche: {total_sources} (nombre de ProductSource)")
    print()
