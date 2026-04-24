"""
Script pour vérifier l'état des variantes en base de données
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from models.product import Product
from models.product_variant import ProductVariant

def check_variants():
    with app.app_context():
        print("\n" + "="*70)
        print("DIAGNOSTIC VARIANTES EN BASE DE DONNÉES")
        print("="*70 + "\n")
        
        # Total variantes
        total_variants = ProductVariant.query.count()
        active_variants = ProductVariant.query.filter_by(active=True).count()
        inactive_variants = ProductVariant.query.filter_by(active=False).count()
        
        print(f"Total variantes: {total_variants}")
        print(f"  - Actives: {active_variants}")
        print(f"  - Inactives: {inactive_variants}")
        
        if total_variants == 0:
            print("\n⚠️  AUCUNE VARIANTE EN BASE DE DONNÉES")
            print("   Les variantes doivent être synchronisées depuis CJ\n")
            return
        
        # Produits avec variantes
        products_with_variants = Product.query.join(ProductVariant).distinct().count()
        print(f"\nProduits avec variantes: {products_with_variants}")
        
        # Exemples de variantes
        print("\n" + "-"*70)
        print("EXEMPLES DE VARIANTES:")
        print("-"*70)
        
        sample_variants = ProductVariant.query.limit(10).all()
        for v in sample_variants:
            product = Product.query.get(v.product_id)
            print(f"\nProduit: {product.name[:50] if product else 'N/A'}")
            print(f"  Variante ID: {v.id}")
            print(f"  CJ VID: {v.cj_vid}")
            print(f"  Couleur: {v.color}")
            print(f"  Taille: {v.size}")
            print(f"  Prix: ${v.price}")
            print(f"  Stock: {v.stock}")
            print(f"  Active: {v.active}")
        
        # Vérifier pourquoi le test ne trouve pas les variantes
        print("\n" + "="*70)
        print("VÉRIFICATION REQUÊTE TEST")
        print("="*70)
        
        test_query = Product.query.join(ProductVariant).filter(
            Product.cj_pid.isnot(None),
            ProductVariant.active == True
        ).distinct().limit(5).all()
        
        print(f"\nRequête test trouve: {len(test_query)} produits")
        
        if len(test_query) == 0:
            print("\n⚠️  PROBLÈME IDENTIFIÉ:")
            
            # Vérifier produits CJ
            cj_products = Product.query.filter(Product.cj_pid.isnot(None)).count()
            print(f"  - Produits CJ: {cj_products}")
            
            # Vérifier variantes actives
            print(f"  - Variantes actives: {active_variants}")
            
            # Vérifier la jointure
            products_with_active_variants = Product.query.join(ProductVariant).filter(
                ProductVariant.active == True
            ).distinct().count()
            print(f"  - Produits avec variantes actives: {products_with_active_variants}")
            
            # Vérifier produits CJ avec variantes actives
            cj_with_variants = Product.query.join(ProductVariant).filter(
                Product.cj_pid.isnot(None),
                ProductVariant.active == True
            ).distinct().count()
            print(f"  - Produits CJ avec variantes actives: {cj_with_variants}")

if __name__ == '__main__':
    check_variants()
