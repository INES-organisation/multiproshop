"""
Script pour activer et publier tous les produits CJ existants
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from models.product import Product
from extensions import db

def activate_all_cj_products():
    """Activer et publier tous les produits CJ"""
    with app.app_context():
        print("=" * 70)
        print("ACTIVATION DE TOUS LES PRODUITS CJ")
        print("=" * 70)
        
        # Récupérer tous les produits CJ inactifs ou non publiés
        inactive_products = Product.query.filter(
            Product.cj_pid.isnot(None),
            db.or_(
                Product.is_active == False,
                Product.published == False
            )
        ).all()
        
        print(f"\n📊 {len(inactive_products)} produits CJ inactifs trouvés\n")
        
        if len(inactive_products) == 0:
            print("✓ Tous les produits CJ sont déjà actifs et publiés!")
            return
        
        # Activer tous les produits
        for product in inactive_products:
            product.is_active = True
            product.published = True
            print(f"  ✓ Activé: {product.name[:60]}")
        
        # Sauvegarder
        db.session.commit()
        
        print("\n" + "=" * 70)
        print(f"✓ {len(inactive_products)} produits activés et publiés")
        print("=" * 70)
        
        # Vérifier le résultat
        total_active = Product.query.filter(
            Product.cj_pid.isnot(None),
            Product.is_active == True,
            Product.published == True
        ).count()
        
        total_cj = Product.query.filter(Product.cj_pid.isnot(None)).count()
        
        print(f"\n📊 RÉSULTAT:")
        print(f"  Total produits CJ: {total_cj}")
        print(f"  Produits actifs et publiés: {total_active}")
        print(f"  Pourcentage: {(total_active/total_cj*100):.1f}%")

if __name__ == '__main__':
    activate_all_cj_products()
    print("\n✅ Activation terminée!")
