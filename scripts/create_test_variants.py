"""
Script pour créer des variantes de test pour les produits existants
Simule des variantes réalistes basées sur les produits
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from models.product import Product
from models.product_variant import ProductVariant
from extensions import db
import random

def create_test_variants():
    with app.app_context():
        print("\n" + "="*80)
        print("CRÉATION DE VARIANTES DE TEST")
        print("="*80 + "\n")
        
        # Couleurs et tailles communes
        colors = ['Black', 'White', 'Red', 'Blue', 'Green', 'Gray', 'Pink', 'Yellow']
        sizes = ['S', 'M', 'L', 'XL', 'XXL']
        
        # Prendre les 10 premiers produits CJ
        products = Product.query.filter(
            Product.cj_pid.isnot(None),
            Product.cost_price.isnot(None)
        ).limit(10).all()
        
        if not products:
            print("❌ Aucun produit trouvé\n")
            return
        
        print(f"Création de variantes pour {len(products)} produits...\n")
        
        total_created = 0
        
        for product in products:
            print(f"\n{'='*80}")
            print(f"Produit: {product.name[:60]}")
            print(f"Prix: ${product.price:.2f} | Coût: ${product.cost_price:.2f}")
            print('='*80)
            
            # Supprimer les anciennes variantes
            old_count = ProductVariant.query.filter_by(product_id=product.id).count()
            if old_count > 0:
                ProductVariant.query.filter_by(product_id=product.id).delete()
                print(f"  ✓ {old_count} anciennes variantes supprimées")
            
            # Créer 3-6 variantes
            num_variants = random.randint(3, 6)
            selected_colors = random.sample(colors, min(num_variants, len(colors)))
            
            created = 0
            for i, color in enumerate(selected_colors):
                # Choisir une taille aléatoire
                size = random.choice(sizes) if random.random() > 0.3 else None
                
                # Variation de prix ±10%
                price_variation = random.uniform(0.9, 1.1)
                variant_price = round(product.price * price_variation, 2)
                
                # Stock aléatoire
                stock = random.randint(5, 50)
                
                # Créer la variante
                variant_key = f"{color}-{size}" if size else color
                
                variant = ProductVariant(
                    product_id=product.id,
                    cj_vid=f"TEST_{product.id}_{i+1}",
                    variant_key=variant_key,
                    color=color,
                    size=size,
                    price=variant_price,
                    suggested_price=product.compare_price,
                    stock=stock,
                    image_url=product.image_url,
                    weight=random.randint(100, 500),
                    sku=f"{product.sku or 'SKU'}-{color[:3].upper()}",
                    active=True
                )
                
                db.session.add(variant)
                created += 1
            
            db.session.commit()
            total_created += created
            
            print(f"  ✓ {created} variantes créées")
            
            # Afficher les variantes
            variants = ProductVariant.query.filter_by(product_id=product.id).all()
            print("\n  Variantes créées:")
            for v in variants:
                display = f"{v.color or 'N/A'} - {v.size or 'N/A'}"
                print(f"    • {display:<20} | ${v.price:.2f} | Stock: {v.stock}")
        
        print("\n" + "="*80)
        print("RÉSUMÉ")
        print("="*80)
        print(f"\nProduits traités: {len(products)}")
        print(f"Total variantes créées: {total_created}")
        
        # Vérification finale
        total_in_db = ProductVariant.query.filter_by(active=True).count()
        products_with_variants = Product.query.join(ProductVariant).filter(
            ProductVariant.active == True
        ).distinct().count()
        
        print(f"Variantes actives en BDD: {total_in_db}")
        print(f"Produits avec variantes: {products_with_variants}")
        
        print("\n✅ Création terminée !")
        print("\nVous pouvez maintenant tester le système de variantes:")
        print("  1. Ouvrir /admin/cj/products")
        print("  2. Cliquer sur un produit pour voir ses variantes")
        print("  3. Tester le sélecteur de variantes sur la page produit\n")

if __name__ == '__main__':
    create_test_variants()
