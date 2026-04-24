"""
Script pour recalculer tous les prix des produits avec les nouvelles marges
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

def recalculate_all_prices():
    with app.app_context():
        print("\n" + "="*80)
        print("RECALCUL DES PRIX AVEC MARGES INTELLIGENTES")
        print("="*80 + "\n")
        
        pricing_service = PricingService()
        
        # Charger la configuration des marges
        import json
        config_file = 'instance/category_markups.json'
        
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                category_markups = config.get('category_markups', {})
                
                # Appliquer les marges au service
                for cat_name, markup in category_markups.items():
                    pricing_service.set_category_markup(cat_name, markup)
                
                print(f"✓ Configuration chargée: {len(category_markups)} catégories\n")
        else:
            print("⚠️  Fichier de configuration non trouvé")
            print("   Lancez d'abord: python scripts/configure_intelligent_margins.py\n")
            return
        
        # Récupérer tous les produits CJ avec cost_price
        products = Product.query.filter(
            Product.cj_pid.isnot(None),
            Product.cost_price.isnot(None),
            Product.cost_price > 0
        ).all()
        
        print(f"Produits à traiter: {len(products)}\n")
        
        if len(products) == 0:
            print("⚠️  Aucun produit avec cost_price trouvé")
            return
        
        # Traiter par lots pour éviter les locks
        batch_size = 50
        total_updated = 0
        total_unchanged = 0
        
        for i in range(0, len(products), batch_size):
            batch = products[i:i+batch_size]
            batch_updated = 0
            
            for product in batch:
                # Récupérer la marge applicable
                markup = pricing_service.get_markup_for_product(product)
                
                # Calculer le nouveau prix
                new_price = pricing_service.calculate_selling_price(
                    product.cost_price, 
                    markup
                )
                
                # Mettre à jour si différent
                old_price = product.price
                if abs(old_price - new_price) > 0.01:  # Éviter les micro-changements
                    product.price = new_price
                    batch_updated += 1
                    total_updated += 1
                else:
                    total_unchanged += 1
            
            # Commit du lot
            try:
                db.session.commit()
                print(f"✓ Lot {i//batch_size + 1}/{(len(products)-1)//batch_size + 1} : {batch_updated}/{len(batch)} produits mis à jour")
            except Exception as e:
                db.session.rollback()
                print(f"✗ Erreur lot {i//batch_size + 1}: {e}")
            
            # Petit délai pour éviter la surcharge
            time.sleep(0.1)
        
        print("\n" + "="*80)
        print("RÉSUMÉ")
        print("="*80)
        print(f"\nTotal produits traités: {len(products)}")
        print(f"Prix mis à jour: {total_updated}")
        print(f"Prix inchangés: {total_unchanged}")
        
        # Afficher quelques exemples par catégorie
        print("\n" + "="*80)
        print("EXEMPLES PAR CATÉGORIE")
        print("="*80 + "\n")
        
        categories_with_products = db.session.query(
            Category.id, 
            Category.name,
            db.func.count(Product.id).label('count')
        ).join(Product).filter(
            Product.cj_pid.isnot(None),
            Product.cost_price.isnot(None)
        ).group_by(Category.id, Category.name).order_by(
            db.func.count(Product.id).desc()
        ).limit(10).all()
        
        for cat_id, cat_name, count in categories_with_products:
            markup = pricing_service.get_markup_for_category(cat_name)
            sample = Product.query.filter_by(category_id=cat_id).filter(
                Product.cost_price.isnot(None)
            ).first()
            
            if sample:
                print(f"\n{cat_name[:50]:<50} | Marge: {markup}%")
                print(f"  Produits: {count}")
                print(f"  Exemple: {sample.name[:60]}")
                print(f"    Coût: ${sample.cost_price:.2f} → Prix: ${sample.price:.2f}")
                
                actual_markup = pricing_service.calculate_markup_percentage(
                    sample.price, 
                    sample.cost_price
                )
                print(f"    Markup réel: {actual_markup:.1f}%")
        
        print("\n✅ Recalcul terminé !\n")

if __name__ == '__main__':
    recalculate_all_prices()
