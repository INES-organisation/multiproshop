"""
Script simple pour vérifier si les produits ont des variantes dans l'API CJ
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from models.product import Product
from models.product_variant import ProductVariant

def check_variants_status():
    with app.app_context():
        print("\n" + "="*70)
        print("DIAGNOSTIC VARIANTES")
        print("="*70 + "\n")
        
        # 1. Vérifier les variantes en BDD
        total_variants = ProductVariant.query.count()
        active_variants = ProductVariant.query.filter_by(active=True).count()
        
        print(f"1. VARIANTES EN BASE DE DONNÉES")
        print(f"   Total: {total_variants}")
        print(f"   Actives: {active_variants}\n")
        
        # 2. Vérifier les produits CJ
        cj_products = Product.query.filter(Product.cj_pid.isnot(None)).count()
        print(f"2. PRODUITS CJ")
        print(f"   Total: {cj_products}\n")
        
        # 3. Vérifier si des produits ont des variantes
        if total_variants > 0:
            products_with_variants = Product.query.join(ProductVariant).filter(
                ProductVariant.active == True
            ).distinct().count()
            print(f"3. PRODUITS AVEC VARIANTES")
            print(f"   Total: {products_with_variants}\n")
            
            # Afficher quelques exemples
            sample_products = Product.query.join(ProductVariant).filter(
                ProductVariant.active == True
            ).distinct().limit(3).all()
            
            for p in sample_products:
                variants = ProductVariant.query.filter_by(
                    product_id=p.id,
                    active=True
                ).all()
                print(f"\n   Produit: {p.name[:50]}")
                print(f"   Variantes: {len(variants)}")
                for v in variants[:3]:
                    print(f"     - {v.color} / {v.size} : ${v.price} (stock: {v.stock})")
        else:
            print("3. ⚠️  AUCUNE VARIANTE SYNCHRONISÉE")
            print("\n   SOLUTION:")
            print("   Les variantes doivent être synchronisées lors de la sync des produits.")
            print("   Vérifiez que le code de synchronisation appelle bien _sync_variants()\n")
            
            # Vérifier un produit exemple
            sample = Product.query.filter(Product.cj_pid.isnot(None)).first()
            if sample:
                print(f"   Exemple de produit CJ: {sample.name[:50]}")
                print(f"   CJ PID: {sample.cj_pid}")
                print(f"   Prix: ${sample.price}")
                print(f"   Stock: {sample.stock}")
                print("\n   Pour synchroniser les variantes, relancez la synchronisation")
                print("   des produits depuis l'interface admin.\n")

if __name__ == '__main__':
    check_variants_status()
