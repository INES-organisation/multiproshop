"""
Corriger les produits orphelins dont la catégorie CJ n'est pas en BDD.
Utilise le categoryName CJ (chemin) quand disponible, sinon analyse le nom du produit.
"""
import sys
import os
import json
import re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.product import Product
from models.category import Category
from extensions import db

app = create_app()

# Mapping du chemin CJ categoryName -> MPS ID
CJ_PATH_TO_MPS = {
    "Women's Clothing": 52,
    "Men's Clothing": 52,
    "Bags & Shoes": 52,
    "Jewelry & Watches": 52,
    "Phones & Accessories": 38,
    "Computer & Office": 22,
    "Home, Garden & Furniture": 67,
    "Health, Beauty & Hair": 87,
    "Automobiles & Motorcycles": 139,
    "Sports & Outdoors": 100,
    "Home Improvement": 152,
    "Pet Supplies": 178,
    "Consumer Electronics": 1,
    "Toys, Kids & Babies": 126,
    "packing material": 67,  # Packaging -> Maison par défaut
}

# Mots-clés pour déterminer la catégorie MPS par le nom du produit
KEYWORD_RULES = [
    # (mots-clés, exclusions, MPS ID)
    # Mode & Vêtements (52)
    (['dress', 'shirt', 'blouse', 'skirt', 'pants', 'jeans', 'jacket', 'coat',
      'sweater', 'hoodie', 'lingerie', 'bra', 'underwear', 'panties', 'bodysuit',
      'swimsuit', 'bikini', 'legging', 'sock', 'scarf', 'hat', 'glove', 'belt',
      'handbag', 'wallet', 'necklace', 'bracelet', 'earring', 'ring', 'jewelry',
      'watch', 'sunglasses', 'shoe', 'boot', 'sneaker', 'sandal', 'slipper',
      'clothing', 'apparel', 'fashion', 'costume', 'romper', 'jumpsuit',
      'cardigan', 'vest', 'polo', 'tee', 't-shirt', 'shorts', 'trouser',
      'kimono', 'robe', 'pajama', 'nightgown', 'corset', 'bustier', 'thong',
      'stocking', 'garter', 'camisole', 'teddy', 'babydoll', 'negligee',
      'wig', 'hair extension', 'hair piece'], [], 52),
    
    # Santé & Beauté (87)
    (['massage', 'massager', 'skincare', 'beauty', 'makeup', 'cosmetic',
      'shampoo', 'cream', 'lotion', 'serum', 'moisturizer', 'cleanser',
      'toothbrush', 'dental', 'health', 'medical', 'thermometer',
      'blood pressure', 'essential oil', 'aromatherapy', 'nail art',
      'manicure', 'pedicure', 'hair dryer', 'straightener', 'curler',
      'trimmer', 'shaver', 'epilator'], [], 87),
    
    # Maison & Jardin (67)
    (['pillow', 'cushion', 'blanket', 'bedding', 'curtain', 'rug', 'carpet',
      'lamp', 'candle', 'vase', 'decoration', 'decor', 'kitchen', 'cooking',
      'baking', 'utensil', 'storage', 'organizer', 'shelf', 'furniture',
      'garden', 'plant', 'flower', 'watering', 'cleaning', 'mop', 'broom',
      'towel', 'bathroom', 'shower', 'soap dispenser', 'trash', 'laundry',
      'iron', 'sewing', 'craft', 'sticker', 'wall art', 'clock',
      'thermometer indoor', 'humidifier', 'air purifier', 'fan',
      'heater', 'vacuum'], ['massage'], 67),
    
    # Informatique (22)
    (['laptop', 'computer', 'keyboard', 'mouse', 'monitor', 'usb', 'cable',
      'adapter', 'charger', 'hub', 'ssd', 'hard drive', 'ram', 'cpu', 'gpu',
      'printer', 'scanner', 'webcam', 'headset', 'speaker', 'microphone',
      'router', 'switch', 'server', 'desk converter', 'office supply',
      'pen holder', 'desk pad'], [], 22),
    
    # Téléphonie (38)
    (['phone case', 'phone holder', 'phone stand', 'screen protector',
      'phone charger', 'power bank', 'earphone', 'earbud', 'airpod',
      'bluetooth', 'wireless charger', 'phone ring', 'phone grip',
      'tablet', 'ipad', 'smartphone', 'sim card', 'phone cable',
      'phone mount', 'car phone'], [], 38),
    
    # Électronique (1)
    (['led strip', 'led light', 'camera', 'drone', 'projector', 'tv',
      'remote control', 'smart home', 'sensor', 'alarm', 'cctv',
      'security camera', 'gps', 'walkie talkie', 'radio',
      'battery', 'solar panel', 'inverter'], [], 1),
    
    # Auto & Moto (139)
    (['car', 'vehicle', 'motorcycle', 'bike', 'tire', 'wheel', 'engine',
      'automotive', 'dashboard', 'windshield', 'bumper', 'headlight',
      'taillight', 'exhaust', 'brake', 'suspension', 'steering',
      'gps car', 'car seat', 'car cover', 'car mat'], [], 139),
    
    # Sports & Loisirs (100)
    (['fitness', 'gym', 'yoga', 'sport', 'exercise', 'workout', 'running',
      'cycling', 'swimming', 'camping', 'hiking', 'fishing', 'hunting',
      'golf', 'tennis', 'basketball', 'football', 'soccer', 'baseball',
      'skateboard', 'surfing', 'diving', 'climbing'], [], 100),
    
    # Animalerie (178)
    (['pet', 'dog', 'cat', 'puppy', 'kitten', 'aquarium', 'fish tank',
      'bird cage', 'hamster', 'rabbit', 'pet food', 'pet toy', 'leash',
      'collar', 'pet bed', 'pet bowl'], [], 178),
    
    # Bébés & Puériculture (113)
    (['baby', 'infant', 'toddler', 'newborn', 'stroller', 'diaper',
      'pacifier', 'bottle feeding', 'nursing', 'maternity', 'pregnant',
      'crib', 'bassinet', 'teether', 'baby monitor'], [], 113),
    
    # Jeux & Jouets (126)
    (['toy', 'puzzle', 'board game', 'action figure', 'doll', 'lego',
      'building block', 'rc car', 'stuffed animal', 'plush',
      'fidget', 'magic trick', 'card game'], [], 126),
    
    # Bricolage (152)
    (['tool', 'drill', 'saw', 'hammer', 'screwdriver', 'wrench', 'plier',
      'tape measure', 'level', 'sandpaper', 'paint', 'brush', 'ladder',
      'pipe', 'valve', 'faucet', 'lock', 'hinge', 'screw', 'bolt',
      'nut', 'washer', 'electrical', 'wire', 'socket', 'switch'], [], 152),
]


def guess_mps_from_name(name):
    """Deviner la catégorie MPS à partir du nom du produit"""
    name_lower = name.lower()
    
    for keywords, exclusions, mps_id in KEYWORD_RULES:
        # Vérifier les exclusions d'abord
        if any(exc in name_lower for exc in exclusions):
            continue
        # Vérifier les mots-clés
        if any(kw in name_lower for kw in keywords):
            return mps_id
    
    return None


def guess_mps_from_cj_path(category_name):
    """Deviner la catégorie MPS à partir du chemin CJ categoryName"""
    if not category_name or category_name == 'INCONNU':
        return None
    
    # Extraire le premier segment du chemin (niveau 1 CJ)
    parts = category_name.split(' > ')
    l1 = parts[0].strip()
    
    for cj_key, mps_id in CJ_PATH_TO_MPS.items():
        if cj_key.lower() in l1.lower():
            return mps_id
    
    return None


with app.app_context():
    products = Product.query.filter(Product.cj_pid.isnot(None)).all()
    
    fixed = 0
    still_orphan = 0
    details = []
    
    for p in products:
        if not p.cj_raw_data:
            continue
        try:
            raw = json.loads(p.cj_raw_data)
        except:
            continue
        
        cj_cat_id = str(raw.get('categoryId') or raw.get('category_id') or '')
        
        if not cj_cat_id:
            # Produit sans categoryId -> deviner par le nom
            target = guess_mps_from_name(p.name)
            if target and p.category_id != target:
                old_cat = Category.query.get(p.category_id)
                new_cat = Category.query.get(target)
                details.append(f"  [NOM] {p.name[:50]} : {old_cat.name if old_cat else '?'} -> {new_cat.name if new_cat else '?'}")
                p.category_id = target
                fixed += 1
            continue
        
        # Vérifier si la catégorie CJ existe en BDD
        cj_cat = Category.query.filter_by(cj_category_id=cj_cat_id).first()
        if cj_cat:
            continue  # Déjà traité par le script principal
        
        # Catégorie CJ non trouvée -> essayer par categoryName puis par nom
        cj_cat_name = raw.get('categoryName', '')
        target = guess_mps_from_cj_path(cj_cat_name)
        
        if not target:
            target = guess_mps_from_name(p.name)
        
        if target:
            if p.category_id != target:
                old_cat = Category.query.get(p.category_id)
                new_cat = Category.query.get(target)
                details.append(f"  [FIX] {p.name[:50]} : {old_cat.name if old_cat else '?'} -> {new_cat.name if new_cat else '?'}")
                p.category_id = target
                fixed += 1
        else:
            still_orphan += 1
            details.append(f"  [???] {p.name[:50]} (CJ: {cj_cat_name}) -> IMPOSSIBLE A DETERMINER")
    
    db.session.commit()
    
    print(f"\n{'='*80}")
    print(f"CORRECTION DES PRODUITS ORPHELINS")
    print(f"{'='*80}\n")
    print(f"Corrigés: {fixed}")
    print(f"Toujours orphelins: {still_orphan}")
    print()
    for d in details:
        print(d)
    
    # Vérification finale
    print(f"\n{'='*80}")
    print(f"DISTRIBUTION FINALE")
    print(f"{'='*80}\n")
    
    from sqlalchemy import func
    dist = Product.query.filter(Product.cj_pid.isnot(None)).with_entities(
        Product.category_id, func.count(Product.id)
    ).group_by(Product.category_id).all()
    
    for cat_id, count in sorted(dist, key=lambda x: x[1], reverse=True):
        cat = Category.query.get(cat_id) if cat_id else None
        name = cat.name if cat else 'AUCUNE'
        print(f"  {name:<35} : {count:>6}")
