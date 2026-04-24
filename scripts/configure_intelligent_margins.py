"""
Script pour configurer des marges intelligentes par catégorie
Basé sur l'analyse du marché et le type de produits
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from models.category import Category
from services.pricing_service import PricingService

def configure_intelligent_margins():
    with app.app_context():
        print("\n" + "="*80)
        print("CONFIGURATION DES MARGES INTELLIGENTES PAR CATÉGORIE")
        print("="*80 + "\n")
        
        pricing_service = PricingService()
        
        # Définition des marges intelligentes par mots-clés
        margin_rules = {
            # Électronique & High-Tech - 40-45%
            40: [
                'Computer', 'Office', 'Laptop', 'Tablet', 'Phone', 'Mobile',
                'Electronics', 'Digital', 'Camera', 'Photo', 'Video',
                'Audio', 'Headphone', 'Speaker', 'Charger', 'Cable',
                'Monitor', 'Keyboard', 'Mouse', 'Printer', 'Scanner'
            ],
            
            # Auto & Moto - 50%
            50: [
                'Auto', 'Car', 'Vehicle', 'Motorcycle', 'Bike',
                'Automotive', 'Motor', 'Engine', 'Tire', 'Wheel'
            ],
            
            # Jouets & Enfants - 55%
            55: [
                'Toy', 'Kids', 'Baby', 'Children', 'Child',
                'Infant', 'Toddler', 'Game', 'Play', 'Puzzle'
            ],
            
            # Maison & Jardin - 60%
            60: [
                'Home', 'House', 'Garden', 'Furniture', 'Decor',
                'Kitchen', 'Dining', 'Bar', 'Cooking', 'Appliance',
                'Textile', 'Bedding', 'Bath', 'Storage', 'Organization',
                'Tool', 'Hardware', 'Improvement', 'Lighting', 'Lamp'
            ],
            
            # Sport & Outdoor - 60%
            60: [
                'Sport', 'Outdoor', 'Fitness', 'Exercise', 'Gym',
                'Camping', 'Hiking', 'Fishing', 'Hunting', 'Cycling',
                'Running', 'Yoga', 'Swimming', 'Athletic'
            ],
            
            # Animaux - 60%
            60: [
                'Pet', 'Dog', 'Cat', 'Animal', 'Bird', 'Fish',
                'Aquarium', 'Cage', 'Leash', 'Collar'
            ],
            
            # Mode & Accessoires - 70%
            70: [
                'Clothing', 'Fashion', 'Apparel', 'Dress', 'Shirt',
                'Pant', 'Skirt', 'Jacket', 'Coat', 'Sweater',
                'Shoe', 'Boot', 'Sandal', 'Sneaker', 'Slipper',
                'Bag', 'Handbag', 'Backpack', 'Wallet', 'Purse',
                'Belt', 'Scarf', 'Hat', 'Cap', 'Glove',
                'Sock', 'Underwear', 'Swimwear', 'Activewear'
            ],
            
            # Beauté & Santé - 70%
            70: [
                'Beauty', 'Cosmetic', 'Makeup', 'Skincare', 'Hair',
                'Health', 'Wellness', 'Personal Care', 'Hygiene',
                'Nail', 'Fragrance', 'Perfume', 'Shampoo', 'Conditioner'
            ],
            
            # Bijoux & Montres - 90%
            90: [
                'Jewelry', 'Jewellery', 'Watch', 'Necklace', 'Bracelet',
                'Ring', 'Earring', 'Pendant', 'Chain', 'Charm',
                'Diamond', 'Gold', 'Silver', 'Pearl', 'Gemstone',
                'Cufflink', 'Brooch', 'Anklet', 'Bangle'
            ]
        }
        
        # Récupérer toutes les catégories CJ
        categories = Category.query.filter(
            Category.cj_category_id.isnot(None)
        ).all()
        
        print(f"Analyse de {len(categories)} catégories...\n")
        
        configured = {}
        for margin, keywords in margin_rules.items():
            configured[margin] = []
        
        default_margin = 60
        default_count = 0
        
        # Appliquer les marges
        for category in categories:
            category_name = category.name or ""
            category_name_lower = category_name.lower()
            
            # Chercher une correspondance
            margin_found = None
            for margin, keywords in margin_rules.items():
                for keyword in keywords:
                    if keyword.lower() in category_name_lower:
                        margin_found = margin
                        break
                if margin_found:
                    break
            
            # Appliquer la marge
            if margin_found:
                pricing_service.set_category_markup(category.name, margin_found)
                configured[margin_found].append(category.name)
            else:
                pricing_service.set_category_markup(category.name, default_margin)
                default_count += 1
        
        # Afficher le résumé
        print("="*80)
        print("RÉSUMÉ DE LA CONFIGURATION")
        print("="*80 + "\n")
        
        total_configured = 0
        for margin in sorted(configured.keys()):
            count = len(configured[margin])
            if count > 0:
                total_configured += count
                print(f"\nMarge {margin}% - {count} catégories:")
                for cat_name in sorted(configured[margin])[:10]:
                    print(f"  • {cat_name[:60]}")
                if count > 10:
                    print(f"  ... et {count - 10} autres")
        
        print(f"\nMarge par défaut ({default_margin}%) - {default_count} catégories")
        print(f"\nTotal: {len(categories)} catégories configurées")
        
        # Sauvegarder dans un fichier de config persistant
        import json
        config_file = 'instance/category_markups.json'
        
        all_markups = {}
        for margin, cat_list in configured.items():
            for cat_name in cat_list:
                all_markups[cat_name] = margin
        
        os.makedirs('instance', exist_ok=True)
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump({
                'default_markup': default_margin,
                'category_markups': all_markups,
                'configured_at': datetime.now().isoformat()
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Configuration sauvegardée dans {config_file}")
        
        print("\n" + "="*80)
        print("PROCHAINE ÉTAPE : Recalculer les prix des produits")
        print("="*80)
        print("\nPour appliquer ces marges aux produits existants, lancez:")
        print("  python scripts/recalculate_all_prices.py")
        print()

if __name__ == '__main__':
    from datetime import datetime
    configure_intelligent_margins()
