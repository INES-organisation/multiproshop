"""
Script pour trouver un produit par SKU et vérifier ses variantes
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from models.product import Product
from models.product_variant import ProductVariant

def find_product():
    with app.app_context():
        sku = "CJYD2648820"
        
        print(f"\nRecherche produit SKU: {sku}\n")
        
        product = Product.query.filter_by(sku=sku).first()
        
        if not product:
            print(f"❌ Produit non trouvé avec SKU {sku}")
            
            # Chercher par CJ PID visible dans la capture
            cj_pid = "2518151919131691100"
            product = Product.query.filter_by(cj_pid=cj_pid).first()
            
            if product:
                print(f"✓ Produit trouvé par CJ PID: {cj_pid}")
            else:
                print(f"❌ Produit non trouvé par CJ PID non plus")
                return
        else:
            print(f"✓ Produit trouvé: {product.name}")
        
        print(f"ID: {product.id}")
        print(f"SKU: {product.sku}")
        print(f"CJ PID: {product.cj_pid}")
        print(f"Prix: ${product.price}")
        
        # Vérifier les variantes
        variants = ProductVariant.query.filter_by(product_id=product.id).all()
        print(f"\nVariantes en BDD: {len(variants)}")
        
        if len(variants) > 0:
            for v in variants:
                print(f"  • {v.color} - {v.size} | ${v.price} | Stock: {v.stock}")
        else:
            print("  ⚠️  Ce produit n'a pas de variantes en BDD")
            print("\n  Pour créer des variantes pour ce produit:")
            print(f"  python scripts/create_single_product_variants.py {product.id}")

if __name__ == '__main__':
    find_product()
