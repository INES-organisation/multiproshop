import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models.api_provider import ApiProvider, ProductSource
from models.product import Product

with app.app_context():
    print("\n" + "="*80)
    print("SYNCHRONISATION DU COMPTEUR DE PRODUITS")
    print("="*80 + "\n")
    
    # Récupérer tous les providers
    providers = ApiProvider.query.all()
    
    for provider in providers:
        # Compter le nombre réel de produits importés depuis ce provider
        real_count = ProductSource.query.filter_by(provider_id=provider.id).count()
        old_count = provider.total_products_imported
        
        # Mettre à jour le compteur
        provider.total_products_imported = real_count
        
        print(f"Provider: {provider.name}")
        print(f"  Ancien compteur: {old_count}")
        print(f"  Nouveau compteur: {real_count}")
        print(f"  Différence: {real_count - old_count}")
        print()
    
    # Sauvegarder les changements
    db.session.commit()
    
    print("="*80)
    print("✓ Compteurs synchronisés avec succès !")
    print("="*80 + "\n")
    
    # Vérification finale
    print("Vérification finale:")
    total = sum(p.total_products_imported for p in providers)
    print(f"Total produits importés (tous providers): {total}")
    print(f"Total produits en base: {Product.query.count()}")
    print()
