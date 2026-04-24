"""
Script sécurisé pour mettre à jour les prix des produits CJ
Fonctionne même avec le serveur Flask actif
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from models.product import Product
from models.category import Category
from services.pricing_service import PricingService
from extensions import db
import time

def update_products_pricing():
    """Mettre à jour les prix de tous les produits CJ par batch"""
    with app.app_context():
        pricing_service = PricingService()
        
        print("=" * 70)
        print("MISE À JOUR DES PRIX PRODUITS CJ")
        print("=" * 70)
        
        # Compter les produits CJ
        total_products = Product.query.filter(
            Product.cj_pid.isnot(None)
        ).count()
        
        print(f"\n📊 {total_products} produits CJ à traiter\n")
        
        updated = 0
        errors = 0
        batch_size = 50
        
        # Traiter par batch pour éviter les locks
        offset = 0
        
        while offset < total_products:
            try:
                # Récupérer un batch de produits
                products = Product.query.filter(
                    Product.cj_pid.isnot(None)
                ).offset(offset).limit(batch_size).all()
                
                if not products:
                    break
                
                # Traiter chaque produit du batch
                for product in products:
                    try:
                        # Le prix actuel devient le cost_price si cost_price est None
                        if product.cost_price is None and product.price:
                            product.cost_price = product.price
                        
                        # Si on a un cost_price, recalculer le prix de vente
                        if product.cost_price and product.cost_price > 0:
                            # Récupérer la catégorie pour la marge
                            category = Category.query.get(product.category_id) if product.category_id else None
                            
                            if category:
                                # Mettre à jour avec le pricing service
                                product = pricing_service.update_product_pricing(
                                    product,
                                    product.cost_price,
                                    product.suggested_price
                                )
                                updated += 1
                                
                                if updated % 10 == 0:
                                    print(f"  ✓ {updated}/{total_products} produits mis à jour...")
                            
                    except Exception as e:
                        errors += 1
                        print(f"  ✗ Erreur produit {product.cj_pid}: {str(e)[:50]}")
                        continue
                
                # Commit le batch
                try:
                    db.session.commit()
                    time.sleep(0.1)  # Petit délai pour éviter les locks
                except Exception as e:
                    db.session.rollback()
                    print(f"  ✗ Erreur commit batch: {str(e)[:50]}")
                    time.sleep(0.5)
                
                offset += batch_size
                
            except Exception as e:
                print(f"  ✗ Erreur batch: {str(e)[:50]}")
                db.session.rollback()
                offset += batch_size
                time.sleep(0.5)
                continue
        
        print("\n" + "=" * 70)
        print(f"✓ {updated} produits mis à jour")
        print(f"✗ {errors} erreurs")
        print("=" * 70)
        
        # Afficher quelques exemples
        print("\n📊 EXEMPLES DE PRODUITS MIS À JOUR:\n")
        
        sample_products = Product.query.filter(
            Product.cj_pid.isnot(None),
            Product.cost_price.isnot(None)
        ).limit(5).all()
        
        for p in sample_products:
            if p.cost_price and p.price:
                profit = p.price - p.cost_price
                margin = (profit / p.price * 100) if p.price > 0 else 0
                
                print(f"  {p.name[:50]:<50}")
                print(f"    Coût: ${p.cost_price:.2f} → Vente: ${p.price:.2f}")
                print(f"    Profit: ${profit:.2f} | Marge: {margin:.1f}%")
                print()
        
        return {
            'total': total_products,
            'updated': updated,
            'errors': errors
        }

if __name__ == '__main__':
    result = update_products_pricing()
    print(f"\n✅ Mise à jour terminée!")
    print(f"\nProduits traités: {result['total']}")
    print(f"Produits mis à jour: {result['updated']}")
    print(f"Erreurs: {result['errors']}")
