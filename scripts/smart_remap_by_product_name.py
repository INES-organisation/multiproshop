"""
Script pour remapper les produits CJ vers les bonnes catégories MPS
en analysant les noms de produits
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from extensions import db
from models.product import Product
from models.category import Category

def get_mps_category_from_product_name(product_name):
    """Déterminer la catégorie MPS à partir du nom du produit"""
    name_lower = product_name.lower()
    
    # Beauté & Santé (ID: 31) - PRIORITÉ HAUTE
    beauty_keywords = [
        'makeup', 'cosmetic', 'lipstick', 'mascara', 'eyeshadow', 'foundation',
        'blush', 'powder', 'concealer', 'eyeliner', 'lip gloss', 'nail polish',
        'skincare', 'cream', 'serum', 'moisturizer', 'cleanser', 'toner',
        'face mask', 'facial', 'beauty', 'perfume', 'fragrance', 'cologne',
        'hair care', 'shampoo', 'conditioner', 'hair oil', 'hair mask',
        'body lotion', 'body wash', 'soap', 'bath', 'spa'
    ]
    
    # Chaussures (ID: 19)
    shoes_keywords = [
        'shoe', 'shoes', 'boot', 'boots', 'sneaker', 'sneakers', 'sandal', 'sandals',
        'slipper', 'slippers', 'heel', 'heels', 'footwear', 'loafer', 'oxford',
        'running shoe', 'basketball shoe', 'tennis shoe'
    ]
    
    # Sacs & Bagages (ID: 20)
    bags_keywords = [
        'bag', 'backpack', 'luggage', 'suitcase', 'wallet', 'purse', 'handbag',
        'shoulder bag', 'crossbody', 'tote', 'clutch', 'messenger bag'
    ]
    
    # Montres (ID: 21)
    watch_keywords = ['watch', 'watches', 'smartwatch', 'timepiece', 'wristwatch']
    
    # Bijoux & Accessoires (ID: 22)
    jewelry_keywords = [
        'jewelry', 'jewellery', 'necklace', 'bracelet', 'ring', 'earring',
        'pendant', 'chain', 'brooch', 'anklet', 'charm'
    ]
    
    # Mode & Vêtements (ID: 13)
    fashion_keywords = [
        'dress', 'shirt', 'blouse', 'top', 'pants', 'trousers', 'jeans',
        'jacket', 'coat', 'sweater', 'hoodie', 'sweatshirt', 'cardigan',
        'skirt', 'shorts', 'suit', 'blazer', 'vest', 't-shirt', 'tee',
        'underwear', 'bra', 'panties', 'boxer', 'sock', 'socks',
        'tie', 'scarf', 'glove', 'gloves', 'hat', 'cap', 'beanie'
    ]
    
    # Maison & Jardin (ID: 23)
    home_keywords = [
        'home decor', 'decoration', 'vase', 'candle', 'frame', 'mirror',
        'curtain', 'blind', 'rug', 'carpet', 'mat', 'pillow', 'cushion',
        'bedding', 'sheet', 'blanket', 'duvet', 'comforter',
        'lamp', 'light', 'lighting', 'chandelier', 'lantern',
        'furniture', 'chair', 'table', 'desk', 'shelf', 'cabinet',
        'kitchen', 'cookware', 'pot', 'pan', 'utensil', 'knife',
        'plate', 'bowl', 'cup', 'mug', 'glass', 'bottle',
        'garden', 'plant', 'flower', 'seed', 'tool', 'hose'
    ]
    
    # Sports & Loisirs (ID: 28)
    sport_keywords = [
        'sport', 'fitness', 'gym', 'exercise', 'yoga', 'workout',
        'dumbbell', 'weight', 'barbell', 'kettlebell', 'resistance band',
        'treadmill', 'bike', 'bicycle', 'cycling', 'running',
        'swimming', 'goggles', 'swimsuit', 'camping', 'tent', 'sleeping bag',
        'hiking', 'backpack', 'fishing', 'rod', 'reel', 'tackle',
        'ball', 'basketball', 'football', 'soccer', 'tennis', 'badminton'
    ]
    
    # Jouets & Enfants (ID: 35)
    toys_keywords = [
        'toy', 'toys', 'doll', 'dolls', 'action figure', 'lego', 'blocks',
        'puzzle', 'game', 'board game', 'card game', 'playset',
        'baby', 'infant', 'toddler', 'kids', 'children',
        'stroller', 'car seat', 'high chair', 'crib', 'nursery',
        'diaper', 'bottle', 'pacifier', 'teether'
    ]
    
    # Auto & Moto (ID: 38)
    auto_keywords = [
        'car', 'auto', 'vehicle', 'automotive', 'motorcycle', 'bike',
        'tire', 'wheel', 'engine', 'motor', 'battery', 'oil',
        'car accessory', 'car cover', 'seat cover', 'floor mat',
        'dash cam', 'gps', 'car charger'
    ]
    
    # Animaux de compagnie (ID: 40)
    pet_keywords = [
        'pet', 'dog', 'cat', 'puppy', 'kitten', 'bird', 'fish',
        'aquarium', 'cage', 'leash', 'collar', 'pet food', 'pet toy'
    ]
    
    # Électronique & High-Tech (ID: 1) - VÉRIFIER EN DERNIER
    electronics_keywords = [
        'phone', 'smartphone', 'iphone', 'samsung', 'android',
        'tablet', 'ipad', 'laptop', 'computer', 'pc', 'macbook',
        'keyboard', 'mouse', 'monitor', 'screen', 'display',
        'camera', 'lens', 'tripod', 'gimbal', 'drone',
        'headphone', 'headphones', 'earphone', 'earphones', 'earbuds',
        'speaker', 'bluetooth speaker', 'soundbar',
        'charger', 'cable', 'adapter', 'power bank',
        'gaming', 'console', 'playstation', 'xbox', 'nintendo', 'switch',
        'controller', 'gamepad', 'joystick',
        'smart watch', 'fitness tracker', 'smart home', 'alexa', 'echo',
        'tv', 'television', 'projector', 'remote'
    ]
    
    # Vérifier dans l'ordre de priorité
    for keyword in beauty_keywords:
        if keyword in name_lower:
            return 31
    
    for keyword in shoes_keywords:
        if keyword in name_lower:
            return 19
    
    for keyword in bags_keywords:
        if keyword in name_lower:
            return 20
    
    for keyword in watch_keywords:
        if keyword in name_lower:
            return 21
    
    for keyword in jewelry_keywords:
        if keyword in name_lower:
            return 22
    
    for keyword in fashion_keywords:
        if keyword in name_lower:
            return 13
    
    for keyword in toys_keywords:
        if keyword in name_lower:
            return 35
    
    for keyword in sport_keywords:
        if keyword in name_lower:
            return 28
    
    for keyword in home_keywords:
        if keyword in name_lower:
            return 23
    
    for keyword in auto_keywords:
        if keyword in name_lower:
            return 38
    
    for keyword in pet_keywords:
        if keyword in name_lower:
            return 40
    
    for keyword in electronics_keywords:
        if keyword in name_lower:
            return 1
    
    # Par défaut: Électronique & High-Tech
    return 1

def smart_remap_products():
    """Remapper intelligemment tous les produits CJ"""
    app = create_app()
    
    with app.app_context():
        print("\n" + "="*80)
        print("REMAPPING INTELLIGENT DES PRODUITS CJ PAR ANALYSE DES NOMS")
        print("="*80 + "\n")
        
        # Récupérer tous les produits CJ
        cj_products = Product.query.filter(Product.cj_pid.isnot(None)).all()
        print(f"Produits CJ à analyser: {len(cj_products)}")
        
        # Statistiques
        remapped_count = 0
        category_stats = {}
        changes = {}
        
        # Analyser chaque produit
        for product in cj_products:
            old_category_id = product.category_id
            
            # Déterminer la nouvelle catégorie
            new_category_id = get_mps_category_from_product_name(product.name)
            
            # Mettre à jour si différent
            if old_category_id != new_category_id:
                product.category_id = new_category_id
                
                # Tracker les changements
                if old_category_id not in changes:
                    changes[old_category_id] = {}
                if new_category_id not in changes[old_category_id]:
                    changes[old_category_id][new_category_id] = 0
                changes[old_category_id][new_category_id] += 1
                
                remapped_count += 1
            
            # Stats
            if new_category_id not in category_stats:
                category_stats[new_category_id] = 0
            category_stats[new_category_id] += 1
            
            if remapped_count % 1000 == 0 and remapped_count > 0:
                print(f"  Analysé: {remapped_count} produits modifiés...")
                db.session.commit()
        
        # Commit final
        db.session.commit()
        
        print(f"\n✅ Analyse terminée: {remapped_count} produits remappés sur {len(cj_products)}")
        
        # Afficher les statistiques
        print("\n" + "="*80)
        print("RÉPARTITION FINALE PAR CATÉGORIE MPS")
        print("="*80 + "\n")
        
        for cat_id, count in sorted(category_stats.items(), key=lambda x: x[1], reverse=True):
            cat = Category.query.get(cat_id)
            if cat:
                print(f"  {cat.name:50} : {count:6} produits")
        
        print("\n" + "="*80)
        print("✅ REMAPPING TERMINÉ AVEC SUCCÈS")
        print("="*80 + "\n")

if __name__ == '__main__':
    smart_remap_products()
