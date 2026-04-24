"""
Activer les produits CJ pour les rendre visibles
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from app import create_app
from models.product import Product
from extensions import db

app = create_app()

with app.app_context():
    print("\n" + "="*70)
    print("ACTIVATION DES PRODUITS CJ")
    print("="*70 + "\n")
    
    # Compter les produits CJ inactifs
    inactive_cj = Product.query.filter(
        Product.cj_pid.isnot(None),
        Product.is_active == False
    ).count()
    
    print(f"Produits CJ inactifs: {inactive_cj}")
    
    if inactive_cj == 0:
        print("Tous les produits CJ sont déjà actifs.")
    else:
        print(f"\nActivation de {inactive_cj} produits CJ...")
        
        # Activer tous les produits CJ
        updated = Product.query.filter(
            Product.cj_pid.isnot(None),
            Product.is_active == False
        ).update({
            'is_active': True,
            'published': True  # Les publier aussi
        })
        
        db.session.commit()
        
        print(f"✓ {updated} produits CJ activés et publiés")
    
    # Vérifier le résultat
    active_cj = Product.query.filter(
        Product.cj_pid.isnot(None),
        Product.is_active == True
    ).count()
    
    published_cj = Product.query.filter(
        Product.cj_pid.isnot(None),
        Product.published == True
    ).count()
    
    print(f"\nRésultat final:")
    print(f"  - Produits CJ actifs: {active_cj}")
    print(f"  - Produits CJ publiés: {published_cj}")
    
    print("\n" + "="*70 + "\n")
