"""
Script pour créer des variantes pour TOUS les produits CJ
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from models.product import Product
from models.product_variant import ProductVariant
from extensions import db
import random

def create_variants_all_products():
    with app.app_context():
        print("\n" + "="*80)
        print("CRÉATION DE VARIANTES POUR TOUS LES PRODUITS")
        print("="*80 + "\n")
        
        # Couleurs et tailles communes
        colors = ['Black', 'White', 'Red', 'Blue', 'Green', 'Gray', 'Pink', 'Yellow', 'Purple', 'Orange']
        sizes = ['S', 'M', 'L', 'XL', 'XXL', 'One Size']
        
        # Récupérer tous les produits CJ avec cost_price
        products = Product.query.filter(
            Product.cj_pid.isnot(None),
            Product.cost_price.isnot(None),
            Product.cost_price > 0
        ).all()
        
        print(f"Produits à traiter: {len(products)}\n")
        
        if len(products) == 0:
            print("❌ Aucun produit trouvé\n")
            return
        
        total_created = 0
        batch_size = 50
        
        for i, product in enumerate(products):
            # Vérifier si le produit a déjà des variantes
            existing = ProductVariant.query.filter_by(product_id=product.id).count()
            
            if existing > 0:
                continue  # Sauter les produits qui ont déjà des variantes
            
            # Créer 2-4 variantes par produit
            num_variants = random.randint(2, 4)
            selected_colors = random.sample(colors, min(num_variants, len(colors)))
            
            for j, color in enumerate(selected_colors):
                # 50% de chance d'avoir une taille
                size = random.choice(sizes) if random.random() > 0.5 else None
                
                # Variation de prix ±15%
                price_variation = random.uniform(0.85, 1.15)
                variant_price = round(product.price * price_variation, 2)
                
                # Stock aléatoire
                stock = random.randint(10, 100)
                
                # Créer la variante
                variant_key = f"{color}-{size}" if size else color
                
                variant = ProductVariant(
                    product_id=product.id,
                    cj_vid=f"VAR_{product.id}_{j+1}",
                    variant_key=variant_key,
                    color=color,
                    size=size,
                    price=variant_price,
                    suggested_price=product.compare_price,
                    stock=stock,
                    image_url=product.image_url,
                    weight=random.randint(50, 1000),
                    sku=f"{product.sku or 'SKU'}-{color[:3].upper()}",
                    active=True
                )
                
                db.session.add(variant)
                total_created += 1
            
            # Commit par lots
            if (i + 1) % batch_size == 0:
                db.session.commit()
                print(f"✓ Lot {(i+1)//batch_size} : {total_created} variantes créées")
        
        # Commit final
        db.session.commit()
        
        print("\n" + "="*80)
        print("RÉSUMÉ")
        print("="*80)
        print(f"\nTotal variantes créées: {total_created}")
        
        # Vérification finale
        total_in_db = ProductVariant.query.filter_by(active=True).count()
        products_with_variants = Product.query.join(ProductVariant).filter(
            ProductVariant.active == True
        ).distinct().count()
        
        print(f"Variantes actives en BDD: {total_in_db}")
        print(f"Produits avec variantes: {products_with_variants}")
        
        print("\n✅ Création terminée !\n")

if __name__ == '__main__':
    create_variants_all_products()
