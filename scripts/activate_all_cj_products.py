"""
Activer et publier tous les produits CJ
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
    
    # Compter les produits
    total = Product.query.filter(Product.cj_pid.isnot(None)).count()
    active = Product.query.filter(
        Product.cj_pid.isnot(None),
        Product.is_active == True
    ).count()
    published = Product.query.filter(
        Product.cj_pid.isnot(None),
        Product.published == True
    ).count()
    
    print(f"Total produits CJ: {total}")
    print(f"  - Actifs: {active}")
    print(f"  - Publiés: {published}")
    print(f"  - À activer: {total - active}")
    
    # Activer et publier tous les produits CJ
    updated = Product.query.filter(
        Product.cj_pid.isnot(None)
    ).update({
        'is_active': True,
        'published': True
    }, synchronize_session=False)
    
    db.session.commit()
    
    print(f"\n✓ {updated} produits mis à jour")
    
    # Vérification
    active_after = Product.query.filter(
        Product.cj_pid.isnot(None),
        Product.is_active == True
    ).count()
    published_after = Product.query.filter(
        Product.cj_pid.isnot(None),
        Product.published == True
    ).count()
    
    print(f"\nAprès activation:")
    print(f"  - Actifs: {active_after}")
    print(f"  - Publiés: {published_after}")
    
    print("\n" + "="*70 + "\n")
