"""
Script de test du PricingService
Teste le calcul automatique des prix avec marges
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

app = create_app()

with app.app_context():
    print("\n" + "="*70)
    print("TEST PRICING SERVICE")
    print("="*70 + "\n")
    
    pricing_service = PricingService()
    
    # Test 1: Calcul de prix simple
    print("1. TEST CALCUL PRIX SIMPLE")
    print("-" * 70)
    
    test_cases = [
        {'cost': 5.50, 'markup': 60, 'expected': 8.99},
        {'cost': 12.00, 'markup': 50, 'expected': 18.99},
        {'cost': 3.25, 'markup': 80, 'expected': 5.85},
        {'cost': 25.00, 'markup': 40, 'expected': 35.99},
    ]
    
    for test in test_cases:
        result = pricing_service.calculate_selling_price(
            test['cost'], 
            test['markup']
        )
        print(f"Prix CJ: ${test['cost']:.2f} | Marge: {test['markup']}% | Prix calculé: ${result:.2f}")
    
    # Test 2: Marges par catégorie
    print("\n2. TEST MARGES PAR CATÉGORIE")
    print("-" * 70)
    
    categories = [
        'Electronics',
        'Fashion',
        'Home & Garden',
        'Jewelry',
        'Unknown Category'
    ]
    
    for cat_name in categories:
        markup = pricing_service.get_markup_for_category(cat_name)
        print(f"{cat_name:30} : {markup}%")
    
    # Test 3: Calcul profit et marge
    print("\n3. TEST CALCUL PROFIT ET MARGE")
    print("-" * 70)
    
    cost = 5.50
    price = 8.99
    profit = pricing_service.calculate_profit(price, cost)
    margin = pricing_service.calculate_margin_percentage(price, cost)
    
    print(f"Prix CJ (coût): ${cost:.2f}")
    print(f"Prix vente: ${price:.2f}")
    print(f"Profit: ${profit:.2f}")
    print(f"Marge: {margin:.2f}%")
    
    # Test 4: Mise à jour prix produits existants
    print("\n4. TEST MISE À JOUR PRODUITS EXISTANTS")
    print("-" * 70)
    
    # Récupérer quelques produits CJ
    products = Product.query.filter(
        Product.cj_pid.isnot(None),
        Product.cost_price.isnot(None)
    ).limit(5).all()
    
    if products:
        print(f"\nProduits trouvés: {len(products)}\n")
        
        for product in products:
            old_price = product.price
            
            # Simuler mise à jour avec PricingService
            markup = pricing_service.get_markup_for_product(product)
            new_price = pricing_service.calculate_selling_price(
                product.cost_price, 
                markup
            )
            
            print(f"Produit: {product.name[:50]}")
            print(f"  Catégorie: {Category.query.get(product.category_id).name if product.category_id else 'N/A'}")
            print(f"  Prix CJ (coût): ${product.cost_price:.2f}")
            print(f"  Marge applicable: {markup}%")
            print(f"  Prix actuel: ${old_price:.2f}")
            print(f"  Prix calculé: ${new_price:.2f}")
            
            if product.compare_price:
                discount = int(((product.compare_price - new_price) / product.compare_price) * 100)
                print(f"  Prix barré: ${product.compare_price:.2f}")
                print(f"  Réduction affichée: -{discount}%")
            
            print()
    else:
        print("Aucun produit CJ avec cost_price trouvé")
    
    # Test 5: Analytics de tarification
    print("\n5. TEST ANALYTICS TARIFICATION")
    print("-" * 70)
    
    analytics = pricing_service.get_pricing_analytics()
    
    print(f"Total produits: {analytics['total_products']}")
    print(f"Prix moyen d'achat: ${analytics['avg_cost_price']:.2f}")
    print(f"Prix moyen de vente: ${analytics['avg_selling_price']:.2f}")
    print(f"Marge moyenne: {analytics['avg_margin_percentage']:.2f}%")
    print(f"Profit potentiel total: ${analytics['total_potential_profit']:.2f}")
    
    print("\nRépartition par tranche de marge:")
    for range_name, count in analytics['products_by_margin_range'].items():
        print(f"  {range_name:10} : {count} produits")
    
    # Test 6: Recalcul des prix (simulation)
    print("\n6. TEST RECALCUL EN MASSE (SIMULATION)")
    print("-" * 70)
    
    print("Simulation du recalcul de tous les prix...")
    print("(Aucune modification en base de données)")
    
    products_to_update = Product.query.filter(
        Product.cj_pid.isnot(None),
        Product.cost_price.isnot(None),
        Product.cost_price > 0
    ).all()
    
    if products_to_update:
        changes = []
        for product in products_to_update:
            markup = pricing_service.get_markup_for_product(product)
            new_price = pricing_service.calculate_selling_price(product.cost_price, markup)
            
            if product.price != new_price:
                changes.append({
                    'name': product.name,
                    'old_price': product.price,
                    'new_price': new_price,
                    'difference': new_price - product.price
                })
        
        print(f"\nProduits à mettre à jour: {len(changes)}/{len(products_to_update)}")
        
        if changes:
            print("\nExemples de changements (5 premiers):")
            for change in changes[:5]:
                print(f"  {change['name'][:40]:40} : ${change['old_price']:.2f} → ${change['new_price']:.2f} ({change['difference']:+.2f})")
    
    print("\n" + "="*70)
    print("✓ Tests terminés")
    print("="*70 + "\n")
