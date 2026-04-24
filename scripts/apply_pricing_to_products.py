"""
Appliquer le calcul de prix avec marges sur tous les produits CJ existants
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from app import create_app
from services.pricing_service import PricingService
from models.product import Product
from models.category import Category
from extensions import db

app = create_app()

with app.app_context():
    print("\n" + "="*70)
    print("APPLICATION DES PRIX AVEC MARGES")
    print("="*70 + "\n")
    
    pricing_service = PricingService()
    
    # Récupérer tous les produits CJ
    products = Product.query.filter(Product.cj_pid.isnot(None)).all()
    
    print(f"Total produits CJ: {len(products)}\n")
    
    if not products:
        print("Aucun produit CJ trouvé")
        exit(0)
    
    # Analyser les produits
    products_with_price = []
    products_without_cost = []
    
    for product in products:
        # Vérifier si le produit a un prix (ancien format)
        if product.price and product.price > 0:
            # Utiliser le prix actuel comme cost_price si cost_price est vide
            if not product.cost_price or product.cost_price == 0:
                product.cost_price = product.price
                products_with_price.append(product)
        else:
            products_without_cost.append(product)
    
    print(f"Produits avec prix (à convertir): {len(products_with_price)}")
    print(f"Produits sans prix: {len(products_without_cost)}")
    
    # Appliquer le calcul de prix
    print("\n" + "-"*70)
    print("APPLICATION DES PRIX")
    print("-"*70 + "\n")
    
    updated_count = 0
    
    for product in products_with_price:
        try:
            # Récupérer la catégorie
            category = Category.query.get(product.category_id) if product.category_id else None
            category_name = category.name if category else "Unknown"
            
            # Récupérer la marge
            markup = pricing_service.get_markup_for_product(product)
            
            # Calculer le nouveau prix
            new_price = pricing_service.calculate_selling_price(product.cost_price, markup)
            
            # Mettre à jour
            old_price = product.price
            product.price = new_price
            
            # Si pas de compare_price, utiliser suggested_price ou calculer
            if not product.compare_price and product.suggested_price:
                product.compare_price = product.suggested_price
            
            updated_count += 1
            
            if updated_count <= 10:  # Afficher les 10 premiers
                print(f"{updated_count}. {product.name[:40]}")
                print(f"   Catégorie: {category_name}")
                print(f"   Prix CJ: ${product.cost_price:.2f}")
                print(f"   Marge: {markup}%")
                print(f"   Ancien prix: ${old_price:.2f}")
                print(f"   Nouveau prix: ${new_price:.2f}")
                if product.compare_price:
                    discount = int(((product.compare_price - new_price) / product.compare_price) * 100)
                    print(f"   Prix barré: ${product.compare_price:.2f} (-{discount}%)")
                print()
        
        except Exception as e:
            print(f"Erreur sur produit {product.id}: {e}")
    
    # Sauvegarder
    print("-"*70)
    print(f"\n{updated_count} produits mis à jour")
    
    response = input("\nSauvegarder les modifications en base de données ? (oui/non): ")
    
    if response.lower() in ['oui', 'o', 'yes', 'y']:
        db.session.commit()
        print("\n✓ Modifications sauvegardées")
        
        # Afficher les analytics
        print("\n" + "="*70)
        print("ANALYTICS APRÈS MISE À JOUR")
        print("="*70 + "\n")
        
        analytics = pricing_service.get_pricing_analytics()
        
        print(f"Total produits: {analytics['total_products']}")
        print(f"Prix moyen d'achat: ${analytics['avg_cost_price']:.2f}")
        print(f"Prix moyen de vente: ${analytics['avg_selling_price']:.2f}")
        print(f"Marge moyenne: {analytics['avg_margin_percentage']:.2f}%")
        print(f"Profit potentiel total: ${analytics['total_potential_profit']:.2f}")
        
        print("\nRépartition par tranche de marge:")
        for range_name, count in analytics['products_by_margin_range'].items():
            print(f"  {range_name:10} : {count} produits")
    else:
        db.session.rollback()
        print("\n✗ Modifications annulées")
    
    print("\n" + "="*70 + "\n")
