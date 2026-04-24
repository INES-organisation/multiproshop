import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models.api_provider import ApiProvider, ProductSource
from models.product import Product

with app.app_context():
    print("\n" + "="*80)
    print("NETTOYAGE ET CORRECTION DU COMPTEUR")
    print("="*80 + "\n")
    
    # 1. Supprimer les ProductSource orphelins
    print("Étape 1: Suppression des ProductSource orphelins...")
    orphans = ProductSource.query.filter(
        ~ProductSource.product_id.in_(db.session.query(Product.id))
    ).all()
    
    print(f"  → {len(orphans)} ProductSource orphelins trouvés")
    
    for orphan in orphans:
        db.session.delete(orphan)
    
    db.session.commit()
    print("  ✓ ProductSource orphelins supprimés")
    print()
    
    # 2. Corriger le compteur pour chaque provider
    print("Étape 2: Correction du compteur de produits...")
    providers = ApiProvider.query.all()
    
    for provider in providers:
        # Compter les Product réels qui ont une ProductSource de ce provider
        real_count = db.session.query(Product).join(
            ProductSource, Product.id == ProductSource.product_id
        ).filter(
            ProductSource.provider_id == provider.id
        ).count()
        
        old_count = provider.total_products_imported
        provider.total_products_imported = real_count
        
        print(f"Provider: {provider.name}")
        print(f"  Ancien compteur: {old_count}")
        print(f"  Nouveau compteur: {real_count}")
        print()
    
    db.session.commit()
    print("  ✓ Compteurs corrigés")
    print()
    
    # 3. Vérification finale
    print("="*80)
    print("VÉRIFICATION FINALE")
    print("="*80 + "\n")
    
    total_products = Product.query.count()
    total_sources = ProductSource.query.count()
    total_counter = sum(p.total_products_imported for p in providers)
    
    print(f"Total Product (produits réels): {total_products}")
    print(f"Total ProductSource (après nettoyage): {total_sources}")
    print(f"Compteur admin (total_products_imported): {total_counter}")
    print()
    
    if total_products == total_sources == total_counter:
        print("✅ TOUT EST SYNCHRONISÉ !")
    else:
        print("⚠️  Il reste des différences:")
        if total_products != total_sources:
            print(f"   - Product vs ProductSource: {total_products} vs {total_sources}")
        if total_products != total_counter:
            print(f"   - Product vs Compteur: {total_products} vs {total_counter}")
    
    print("\n" + "="*80 + "\n")
