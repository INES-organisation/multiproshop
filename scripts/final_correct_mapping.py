"""
Script de remapping final avec les VRAIS IDs de catégories MPS
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from extensions import db
from models.product import Product
from models.category import Category

# VRAIS IDs des catégories MPS principales
CATEGORY_IDS = {
    'electronique': 1,      # Électronique & High-Tech
    'informatique': 22,     # Informatique
    'telephonie': 38,       # Téléphonie & Tablettes
    'mode': 52,             # Mode & Vêtements
    'maison': 67,           # Maison & Jardin
    'beaute': 87,           # Santé & Beauté
    'sport': 100,           # Sports & Loisirs
    'bebe': 113,            # Bébés & Puériculture
    'jouets': 126,          # Jeux & Jouets
    'auto': 139,            # Auto & Moto
    'bricolage': 152,       # Bricolage & Outillage
    'alimentation': 165,    # Alimentation & Boissons
    'animaux': 178,         # Animalerie
    'livres': 191,          # Livres & Papeterie
    'culture': 200,         # Culture & Divertissement
}

def get_correct_category(product_name):
    """Déterminer la catégorie correcte avec les vrais IDs"""
    name_lower = product_name.lower()
    
    # Beauté & Santé (ID: 87) - PRIORITÉ MAXIMALE
    beauty_keywords = [
        'makeup', 'cosmetic', 'lipstick', 'mascara', 'eyeshadow', 'foundation',
        'blush', 'powder', 'concealer', 'eyeliner', 'lip gloss', 'nail polish',
        'skincare', 'cream', 'serum', 'moisturizer', 'cleanser', 'toner',
        'face mask', 'facial', 'beauty', 'perfume', 'fragrance', 'cologne',
        'hair care', 'shampoo', 'conditioner', 'hair oil', 'hair mask',
        'body lotion', 'body wash', 'soap', 'bath', 'spa'
    ]
    
    # Maison & Jardin (ID: 67) - HAUTE PRIORITÉ
    home_keywords = [
        'furniture', 'chair', 'table', 'desk', 'shelf', 'cabinet', 'sofa', 'couch',
        'bed', 'mattress', 'wardrobe', 'dresser', 'nightstand',
        'home decor', 'decoration', 'vase', 'candle', 'frame', 'mirror',
        'curtain', 'blind', 'rug', 'carpet', 'mat', 'pillow', 'cushion',
        'bedding', 'sheet', 'blanket', 'duvet', 'comforter',
        'lamp', 'light', 'lighting', 'chandelier', 'lantern', 'ceiling light',
        'kitchen', 'cookware', 'pot', 'pan', 'utensil', 'knife',
        'plate', 'bowl', 'cup', 'mug', 'glass', 'bottle',
        'garden', 'plant', 'flower', 'seed', 'planter', 'raised bed',
        'outdoor', 'patio', 'chaise lounge', 'lawn', 'trellis'
    ]
    
    # Mode & Vêtements (ID: 52) - HAUTE PRIORITÉ
    fashion_keywords = [
        # Vêtements femme
        'womens', 'women', 'ladies', 'dress', 'blouse', 'skirt',
        # Vêtements général
        'shirt', 'top', 'pants', 'trousers', 'jeans',
        'jacket', 'coat', 'sweater', 'hoodie', 'sweatshirt', 'cardigan',
        'shorts', 'suit', 'blazer', 'vest', 't-shirt', 'tee',
        'underwear', 'bra', 'panties', 'boxer', 'sock', 'socks',
        'romper', 'jumpsuit', 'onesie', 'bodysuit',
        # Accessoires vestimentaires
        'tie', 'scarf', 'glove', 'gloves', 'hat', 'cap', 'beanie',
        # Chaussures
        'shoe', 'shoes', 'boot', 'boots', 'sneaker', 'sneakers',
        'sandal', 'sandals', 'slipper', 'slippers', 'heel', 'heels',
        'flat', 'flats', 'ballet flat', 'loafer', 'oxford',
        # Sacs et accessoires
        'bag', 'backpack', 'handbag', 'purse', 'wallet',
        # Bijoux et montres
        'watch', 'watches', 'jewelry', 'necklace', 'bracelet', 'ring', 'earring'
    ]
    
    # Bébés & Puériculture (ID: 113)
    baby_keywords = [
        'baby clothes', 'baby romper', 'baby onesie', 'baby bodysuit',
        'infant', 'toddler', 'newborn',
        'stroller', 'high chair', 'crib', 'nursery',
        'diaper', 'baby bottle', 'pacifier', 'teether',
        'baby floor socks', 'baby socks'
    ]
    
    # Jeux & Jouets (ID: 126)
    toys_keywords = [
        'plush toy', 'stuffed toy', 'toy doll',
        'action figure', 'lego', 'building blocks', 'magnetic tiles',
        'puzzle toy', 'board game', 'card game', 'playset',
        'rc car', 'drone toy', 'robot toy',
        'rocking horse', 'ride-on toy', 'fidget toy',
        'cat toy', 'dog toy', 'pet toy',
        'kids toy', 'children toy', 'toy building set'
    ]
    
    # Sports & Loisirs (ID: 100)
    sport_keywords = [
        'fitness', 'gym', 'exercise', 'workout',
        'dumbbell', 'weight', 'barbell', 'kettlebell', 'resistance band',
        'treadmill', 'cycling', 'bicycle speed',
        'swimming goggles', 'camping tent', 'sleeping bag',
        'fishing rod', 'fishing reel', 'fishing tackle',
        'basketball', 'football', 'soccer ball', 'tennis', 'badminton',
        'foam roller', 'yoga mat', 'canopy tent', 'umbrella base'
    ]
    
    # Auto & Moto (ID: 139)
    auto_keywords = [
        'car', 'auto', 'vehicle', 'automotive', 'motorcycle',
        'tire', 'wheel', 'engine', 'motor', 'battery',
        'car accessory', 'car cover', 'seat cover', 'floor mat',
        'dash cam', 'car charger', 'diagnostic', 'scanner'
    ]
    
    # Animalerie (ID: 178) - ATTENTION: vérifier contexte pour éviter faux positifs
    pet_keywords = [
        'pet food', 'pet toy', 'dog food', 'cat food',
        'dog collar', 'cat collar', 'pet leash', 'dog leash',
        'puppy', 'kitten', 'bird cage', 'fish tank',
        'aquarium', 'pet bed', 'pet carrier'
    ]
    
    # Téléphonie & Tablettes (ID: 38)
    phone_keywords = [
        'phone', 'smartphone', 'iphone', 'samsung', 'android',
        'tablet', 'ipad', 'phone case', 'screen protector'
    ]
    
    # Informatique (ID: 22) - Ordinateurs et composants
    computer_keywords = [
        'laptop', 'computer', 'pc', 'macbook', 'desktop',
        'keyboard', 'mouse', 'gaming mouse', 'wireless mouse', 'usb mouse',
        'monitor', 'screen', 'display',
        'processor', 'cpu', 'gpu', 'ram', 'memory', 'ssd', 'hard drive',
        'motherboard', 'graphics card', 'power supply', 'backboard'
    ]
    
    # Électronique & High-Tech (ID: 1) - Gadgets et accessoires
    electronics_keywords = [
        'camera', 'lens', 'tripod', 'gimbal', 'drone',
        'headphone', 'headphones', 'earphone', 'earphones', 'earbuds',
        'speaker', 'bluetooth speaker', 'soundbar',
        'charger', 'cable', 'adapter', 'power bank',
        'gaming', 'console', 'playstation', 'xbox', 'nintendo', 'switch',
        'controller', 'gamepad', 'joystick',
        'smart watch', 'fitness tracker', 'smart home', 'alexa', 'echo',
        'tv', 'television', 'projector', 'remote', 'printer'
    ]
    
    # Vérifier dans l'ordre de priorité (du plus spécifique au plus général)
    for keyword in beauty_keywords:
        if keyword in name_lower:
            return CATEGORY_IDS['beaute']
    
    for keyword in home_keywords:
        if keyword in name_lower:
            return CATEGORY_IDS['maison']
    
    # Mode & Vêtements AVANT Jouets et Sport pour éviter les faux positifs
    for keyword in fashion_keywords:
        if keyword in name_lower:
            return CATEGORY_IDS['mode']
    
    for keyword in baby_keywords:
        if keyword in name_lower:
            return CATEGORY_IDS['bebe']
    
    # Auto AVANT Jouets pour capturer les clés de voiture et accessoires
    for keyword in auto_keywords:
        if keyword in name_lower:
            return CATEGORY_IDS['auto']
    
    for keyword in toys_keywords:
        if keyword in name_lower:
            return CATEGORY_IDS['jouets']
    
    for keyword in sport_keywords:
        if keyword in name_lower:
            return CATEGORY_IDS['sport']
    
    # IMPORTANT: Vérifier téléphonie, informatique et électronique AVANT animalerie
    # pour éviter les faux positifs (ex: "mouse" = souris informatique, pas animal)
    for keyword in phone_keywords:
        if keyword in name_lower:
            return CATEGORY_IDS['telephonie']
    
    for keyword in computer_keywords:
        if keyword in name_lower:
            return CATEGORY_IDS['informatique']
    
    for keyword in electronics_keywords:
        if keyword in name_lower:
            return CATEGORY_IDS['electronique']
    
    # Animalerie en dernier pour éviter les faux positifs
    for keyword in pet_keywords:
        if keyword in name_lower:
            return CATEGORY_IDS['animaux']
    
    # Par défaut: Électronique & High-Tech
    return CATEGORY_IDS['electronique']

def final_correct_mapping():
    """Remapping final avec les bons IDs"""
    app = create_app()
    
    with app.app_context():
        print("\n" + "="*80)
        print("REMAPPING FINAL AVEC LES VRAIS IDs DE CATÉGORIES MPS")
        print("="*80 + "\n")
        
        # Récupérer tous les produits CJ
        cj_products = Product.query.filter(Product.cj_pid.isnot(None)).all()
        print(f"Produits CJ à remapper: {len(cj_products)}")
        
        # Statistiques
        remapped_count = 0
        category_stats = {}
        
        # Remapper chaque produit
        for product in cj_products:
            # Déterminer la catégorie correcte
            correct_category_id = get_correct_category(product.name)
            
            # Mettre à jour
            product.category_id = correct_category_id
            
            # Stats
            if correct_category_id not in category_stats:
                category_stats[correct_category_id] = 0
            category_stats[correct_category_id] += 1
            
            remapped_count += 1
            
            if remapped_count % 1000 == 0:
                print(f"  Remappé: {remapped_count}/{len(cj_products)} produits...")
                db.session.commit()
        
        # Commit final
        db.session.commit()
        
        print(f"\n✅ Remapping terminé: {remapped_count} produits remappés")
        
        # Afficher les statistiques
        print("\n" + "="*80)
        print("RÉPARTITION FINALE PAR CATÉGORIE MPS")
        print("="*80 + "\n")
        
        for cat_id, count in sorted(category_stats.items(), key=lambda x: x[1], reverse=True):
            cat = Category.query.get(cat_id)
            if cat:
                print(f"  {cat.name:50} : {count:6} produits")
        
        print("\n" + "="*80)
        print("✅ REMAPPING FINAL TERMINÉ")
        print("="*80 + "\n")

if __name__ == '__main__':
    final_correct_mapping()
