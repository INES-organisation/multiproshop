"""
Script pour configurer les marges optimisées pour toutes les catégories CJ
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from models.category import Category
from services.pricing_service import PricingService
from extensions import db

# Configuration des marges par catégorie (optimisées pour la compétitivité)
CATEGORY_MARKUPS = {
    # Électronique & Tech (marges faibles - haute concurrence)
    'Electronics': 50,
    'Computer & Office': 50,
    'Consumer Electronics': 50,
    'Security & Protection': 55,
    'Lights & Lighting': 55,
    'Camera & Photo': 55,
    'Video Games': 60,
    'Smart Electronics': 55,
    'Electronic Components & Supplies': 50,
    
    # Mode & Accessoires (marges élevées - forte valeur perçue)
    'Fashion': 80,
    "Women's Clothing": 85,
    "Men's Clothing": 75,
    'Shoes': 70,
    'Bags & Luggage': 75,
    'Jewelry & Watches': 100,
    'Jewelry': 100,
    'Watches': 90,
    'Accessories': 80,
    'Novelty & Special Use': 85,
    
    # Maison & Jardin (marges moyennes-élevées)
    'Home & Garden': 70,
    'Home Improvement': 65,
    'Furniture': 75,
    'Home Decor': 80,
    'Kitchen, Dining & Bar': 65,
    'Home Appliances': 60,
    'Garden Supplies': 70,
    'Household Merchandises': 70,
    'Home Textile': 75,
    
    # Beauté & Santé (marges élevées)
    'Health, Beauty & Hair': 75,
    'Beauty & Health': 75,
    'Hair Extensions & Wigs': 85,
    'Makeup': 80,
    'Skin Care': 75,
    'Health Care': 70,
    'Personal Care': 70,
    
    # Enfants & Bébés (marges moyennes)
    'Toys, Kids & Babies': 60,
    'Toys & Hobbies': 65,
    'Mother & Kids': 70,
    'Baby Products': 65,
    
    # Sports & Loisirs (marges moyennes)
    'Sports & Outdoors': 65,
    'Sports & Entertainment': 65,
    'Outdoor Fun & Sports': 65,
    'Camping & Hiking': 70,
    'Cycling': 60,
    'Fishing': 65,
    
    # Animaux (marges moyennes-élevées)
    'Pet Supplies': 65,
    'Dog Supplies': 65,
    'Cat Supplies': 65,
    
    # Automobile & Moto (marges moyennes)
    'Automobiles & Motorcycles': 60,
    'Car Accessories': 65,
    'Motorcycle Accessories': 65,
    'Auto Replacement Parts': 55,
    
    # Outils & Bricolage (marges moyennes)
    'Tools': 60,
    'Tools & Home Improvement': 60,
    'Hand Tools': 55,
    'Power Tools': 55,
    'Measurement & Analysis Instruments': 60,
    
    # Téléphones & Accessoires (marges moyennes)
    'Phones & Accessories': 60,
    'Phone Accessories': 65,
    'Mobile Phone Accessories': 65,
    'Communication Equipment': 55,
    
    # Bureau & École (marges moyennes)
    'Office & School Supplies': 65,
    'Stationery': 70,
    'Art Supplies': 70,
    
    # Autres catégories (marges moyennes)
    'Luggage & Bags': 75,
    'Weddings & Events': 80,
    'Gifts & Crafts': 75,
    'Festive & Party Supplies': 80,
    'Musical Instruments': 65,
    'Books': 50,
    'Food': 40,
    'Underwear & Sleepwears': 75,
}

def configure_markups():
    """Configurer les marges pour toutes les catégories"""
    with app.app_context():
        pricing_service = PricingService()
        
        print("=" * 70)
        print("CONFIGURATION DES MARGES PAR CATÉGORIE")
        print("=" * 70)
        
        # Récupérer toutes les catégories CJ
        categories = Category.query.filter(
            Category.cj_category_id.isnot(None)
        ).order_by(Category.level, Category.name).all()
        
        configured_count = 0
        default_count = 0
        
        print(f"\n📊 {len(categories)} catégories CJ trouvées\n")
        
        for category in categories:
            # Chercher une marge configurée
            markup = None
            
            # Essayer correspondance exacte
            if category.name in CATEGORY_MARKUPS:
                markup = CATEGORY_MARKUPS[category.name]
            # Essayer correspondance partielle
            else:
                for key, value in CATEGORY_MARKUPS.items():
                    if key.lower() in category.name.lower() or category.name.lower() in key.lower():
                        markup = value
                        break
            
            if markup:
                pricing_service.set_category_markup(category.name, markup)
                configured_count += 1
                print(f"✓ {category.name:<40} → {markup:>3}% (Level {category.level})")
            else:
                # Utiliser marge par défaut selon le niveau
                if category.level == 1:
                    default_markup = 60
                elif category.level == 2:
                    default_markup = 65
                else:
                    default_markup = 70
                
                pricing_service.set_category_markup(category.name, default_markup)
                default_count += 1
                print(f"○ {category.name:<40} → {default_markup:>3}% (défaut L{category.level})")
        
        print("\n" + "=" * 70)
        print(f"✓ {configured_count} catégories avec marges spécifiques")
        print(f"○ {default_count} catégories avec marges par défaut")
        print(f"📊 Total: {len(categories)} catégories configurées")
        print("=" * 70)
        
        return {
            'total': len(categories),
            'configured': configured_count,
            'default': default_count
        }

if __name__ == '__main__':
    result = configure_markups()
    print(f"\n✅ Configuration terminée!")
    print(f"\nPour appliquer ces marges aux produits existants:")
    print(f"python scripts/apply_pricing_auto.py")
