"""
Supprimer tous les produits non-CJ pour cohérence
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from app import create_app
from models.product import Product
from models.product_variant import ProductVariant
from extensions import db

app = create_app()

with app.app_context():
    print("\n" + "="*70)
    print("SUPPRESSION DES PRODUITS NON-CJ")
    print("="*70 + "\n")
    
    # 1. Compter les produits
    total_products = Product.query.count()
    cj_products = Product.query.filter(Product.cj_pid.isnot(None)).count()
    non_cj_products = Product.query.filter(Product.cj_pid.is_(None)).count()
    
    print(f"Total produits: {total_products}")
    print(f"  - Produits CJ: {cj_products}")
    print(f"  - Produits non-CJ: {non_cj_products}")
    
    if non_cj_products == 0:
        print("\n✓ Aucun produit non-CJ à supprimer")
        print("\n" + "="*70 + "\n")
        exit(0)
    
    print(f"\n⚠️  {non_cj_products} produits non-CJ vont être supprimés")
    print("\nSuppression en cours...")
    
    # 2. Supprimer les variantes des produits non-CJ
    non_cj_product_ids = [p.id for p in Product.query.filter(Product.cj_pid.is_(None)).all()]
    
    if non_cj_product_ids:
        variants_deleted = ProductVariant.query.filter(
            ProductVariant.product_id.in_(non_cj_product_ids)
        ).delete(synchronize_session=False)
        
        print(f"  - {variants_deleted} variantes supprimées")
    
    # 3. Supprimer les produits non-CJ
    deleted = Product.query.filter(Product.cj_pid.is_(None)).delete(synchronize_session=False)
    
    db.session.commit()
    
    print(f"  - {deleted} produits supprimés")
    
    # 4. Vérification
    remaining = Product.query.count()
    remaining_cj = Product.query.filter(Product.cj_pid.isnot(None)).count()
    
    print(f"\n✓ Suppression terminée")
    print(f"\nProduits restants: {remaining}")
    print(f"  - Tous sont des produits CJ: {remaining == remaining_cj}")
    
    print("\n" + "="*70 + "\n")
