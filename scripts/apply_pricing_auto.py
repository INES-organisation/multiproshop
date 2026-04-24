"""
Appliquer automatiquement le calcul de prix avec marges sur tous les produits CJ
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
    print("APPLICATION AUTOMATIQUE DES PRIX AVEC MARGES")
    print("="*70 + "\n")
    
    pricing_service = PricingService()
    
    # Récupérer tous les produits CJ
    products = Product.query.filter(Product.cj_pid.isnot(None)).all()
    
    print(f"Total produits CJ: {len(products)}\n")
    
    if not products:
        print("Aucun produit CJ trouvé")
        exit(0)
    
    # Appliquer le calcul de prix
    updated_count = 0
    
    for product in products:
        try:
            # Si le produit a un prix mais pas de cost_price, utiliser price comme cost_price
            if product.price and product.price > 0:
                if not product.cost_price or product.cost_price == 0:
                    product.cost_price = product.price
            
            # Si on a un cost_price, calculer le nouveau prix
            if product.cost_price and product.cost_price > 0:
                # Récupérer la marge
                markup = pricing_service.get_markup_for_product(product)
                
                # Calculer le nouveau prix
                new_price = pricing_service.calculate_selling_price(product.cost_price, markup)
                
                # Mettre à jour
                product.price = new_price
                
                # Si pas de compare_price, utiliser suggested_price
                if not product.compare_price and product.suggested_price:
                    product.compare_price = product.suggested_price
                
                updated_count += 1
        
        except Exception as e:
            print(f"Erreur sur produit {product.id}: {e}")
    
    # Sauvegarder
    db.session.commit()
    
    print(f"✓ {updated_count} produits mis à jour et sauvegardés")
    
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
    
    # Top 10 produits par profit
    print("\n" + "-"*70)
    print("TOP 10 PRODUITS PAR PROFIT")
    print("-"*70 + "\n")
    
    top_products = Product.query.filter(
        Product.cj_pid.isnot(None),
        Product.cost_price.isnot(None),
        Product.price.isnot(None)
    ).all()
    
    # Calculer le profit pour chaque produit
    products_with_profit = []
    for p in top_products:
        profit = pricing_service.calculate_profit(p.price, p.cost_price)
        if profit > 0:
            products_with_profit.append({
                'name': p.name,
                'cost': p.cost_price,
                'price': p.price,
                'profit': profit
            })
    
    # Trier par profit décroissant
    products_with_profit.sort(key=lambda x: x['profit'], reverse=True)
    
    for i, p in enumerate(products_with_profit[:10], 1):
        print(f"{i:2}. {p['name'][:45]:45} | Coût: ${p['cost']:6.2f} | Prix: ${p['price']:6.2f} | Profit: ${p['profit']:5.2f}")
    
    print("\n" + "="*70 + "\n")
