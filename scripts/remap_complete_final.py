"""
Remapping COMPLET et FINAL de tous les produits CJ.
Gère les deux formats de categoryId dans cj_raw_data :
  - 'categoryId' (camelCase, format API CJ v1)
  - 'category_id' (underscore, format API CJ v2/sync)

Logique : CJ L3 override > CJ L2 override > CJ L1 default > nom du produit
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.product import Product
from models.category import Category
from extensions import db

app = create_app()

# ============================================================
# MAPPING CJ L1 -> MPS
# ============================================================
CJ_L1_TO_MPS = {
    'Phones & Accessories': 38,
    'Computer & Office': 22,
    'Home, Garden & Furniture': 67,
    "Women's Clothing": 52,
    'Jewelry & Watches': 52,
    "Men's Clothing": 52,
    'Bags & Shoes': 52,
    'Health, Beauty & Hair': 87,
    'Automobiles & Motorcycles': 139,
    'Sports & Outdoors': 100,
    'Home Improvement': 152,
    'Pet Supplies': 178,
    'Consumer Electronics': 1,
    'Toys, Kids & Babies': 126,
}

# ============================================================
# OVERRIDES CJ L2 -> MPS
# ============================================================
CJ_L2_OVERRIDES = {
    'Swimming': 52, 'Sneakers': 52, 'Sportswear': 52,
    'LED Lighting': 67, 'Indoor Lighting': 67, 'Outdoor Lighting': 67, 'Home Appliances': 67,
    'Baby Clothing': 113, 'Baby & Mother': 113,
    'Boys Clothing': 52, 'Girls Clothing': 52, 'Shoes & Bags': 52,
    'Video Games': 126,
    'Desks & Chairs': 67,
    "Men's Luggage & Bags": 52, "Women's Luggage & Bags": 52,
    'Functional Bags': 52, "Men's Shoes": 52, "Women's Shoes": 52,
}

# ============================================================
# OVERRIDES CJ L3 -> MPS
# ============================================================
CJ_L3_OVERRIDES = {
    'Bikini Sets': 52, 'One-Piece Suits': 52, 'Two-Piece Suits': 52, 'Cover-Ups': 52,
    'Camping & Hiking': 67,  # Gazebos, chaises longues, etc.
    'Flashlights & Torches': 152,
    'Garden Tools': 67, 'Watering & Irrigation': 67,
}

# ============================================================
# RÈGLES PAR NOM (pour les orphelins sans catégorie CJ)
# Ordre = priorité (tech avant mode)
# ============================================================
NAME_RULES = [
    (['pet ', 'dog ', 'cat toy', 'cat bed', 'cat tree', 'bird bath',
      'chicken water', 'poultry', 'cat harness', 'dog kennel',
      'rabbit hutch', 'bird cage', 'pet food', 'pet bowl',
      'pet bed', 'pet collar', 'pet leash', 'aquarium'], 178),
    (['car wash', 'car seat', 'car cover', 'car mat', 'car mirror',
      'car light', 'car charger', 'dashboard', 'windshield', 'bumper',
      'headlight', 'taillight', 'exhaust', 'brake pad', 'suspension',
      'steering', 'wiper', 'rearview mirror', 'rv roof vent',
      'door mirror', 'sunshade', 'grille', 'oil film remover',
      'motorcycle', 'automotive', 'car roof', 'car phone', 'visor',
      'car glass', 'heat shrink wire connector'], 139),
    (['phone case', 'phone holder', 'screen protector', 'power bank',
      'earphone', 'earbud', 'airpod', 'wireless charger', 'phone ring',
      'phone grip', 'phone mount', 'phone cable', 'phone stand',
      'tablet case', 'ipad case', 'sim card', 'phone bracket',
      'data cable', 'charging cable', 'lightning adapter',
      'usb cable', 'type-c', 'otg adapter', 'audio cable',
      'headphone case', 'earphone case', 'magnetic wire', 'audio antenna'], 38),
    (['laptop', 'notebook', 'computer', 'keyboard', 'mouse pad',
      'monitor', 'usb hub', 'ssd', 'hard drive', 'printer', 'webcam',
      'desk converter', 'office desk', 'computer desk', 'pc ',
      'laptop stand', 'laptop bracket', 'laptop cooling', 'laptop radiator',
      'notebook bracket', 'notebook cooling', 'notebook radiator',
      'computer bracket', 'computer stand', 'computer cooling',
      'tablet stand', 'tablet bracket', 'tablet holder',
      'laptop bag', 'laptop sleeve', 'laptop case',
      'computer jacket', 'computer bag'], 22),
    (['drone', 'projector', 'camera', 'cctv', 'security cam',
      'bluetooth speaker', 'bluetooth earbuds', 'bluetooth headset',
      'bluetooth headphone', 'bluetooth helmet', 'bluetooth 5',
      'wireless speaker', 'wireless headphone', 'wireless earphone',
      'wireless ear-hook', 'wireless earbuds',
      'digital camera', 'infrared camera', 'hunting camera',
      'amplifier', 'noise-canceling', 'stereo wireless',
      'smart glasses', 'karaoke', 'subwoofer', 'ktv',
      'air cooler', 'air conditioner fan',
      'led strip', 'led light', 'smart home',
      'remote control', 'alarm system', 'telescoping rod',
      'laser level', 'portable lamp rgb'], 1),
    (['massage', 'massager', 'fascial gun', 'moisturizing', 'hydrating',
      'skin care', 'beauty tool', 'cosmetic', 'cream', 'serum',
      'shampoo', 'lotion', 'nail art', 'hair dryer', 'straightener',
      'curler', 'trimmer', 'shaver', 'essential oil', 'face mask',
      'blood pressure', 'thermometer', 'health care',
      'supplement', 'vitamin', 'capsule', 'toothbrush',
      'scrubber', 'photon skin', 'rejuvenation', 'therapeutic',
      'infrared sweat', 'lumbar support', 'heated waist',
      'heating waist', 'creatine', 'gummies'], 87),
    (['baby', 'infant', 'toddler', 'newborn', 'stroller', 'diaper',
      'pacifier', 'nursing', 'maternity'], 113),
    (['toy ', 'toys ', 'puzzle', 'plush', 'doll', 'fidget',
      'building block', 'rc car', 'board game', 'action figure'], 126),
    (['fitness', 'gym ', 'yoga ', 'exercise', 'workout', 'treadmill',
      'barbell', 'dumbbell', 'resistance band', 'ab wheel', 'foam roller',
      'pelvic floor', 'spinning fitness', 'calf raise', 'strength training',
      'camping chair', 'camping tent', 'canopy tent', 'hiking',
      'fishing', 'golf ', 'tennis', 'basketball', 'football', 'soccer',
      'cycling', 'bicycle saddle', 'bike ', 'trout bait',
      'beach canopy', 'outdoor solar', 'marathon', 'running vest',
      'boxing', 'bottle cage', 'sports bluetooth',
      'petrol can', 'fuel oil', 'gasoline bucket', 'drag harrow',
      'creeper garage'], 100),
    (['drill', 'saw ', 'hammer', 'screwdriver', 'wrench', 'plier',
      'tool set', 'sandpaper', 'paint brush', 'crimping',
      'flashlight', 'torch ', 'airbrush', 'tool case',
      'combination tool', 'leaf blower', 'chip tool',
      'shovel', 'hex wrench', 'high carbon steel'], 152),
    (['garden', 'planter', 'greenhouse', 'grow house', 'flower stand',
      'plant stand', 'gazebo', 'porch swing', 'lounge chair',
      'chaise lounge', 'folding lounge', 'umbrella base', 'pergola',
      'wood panel', 'metal arch', 'topiary', 'cold frame',
      'crop cage', 'raised bed', 'compost', 'hammock',
      'beach set', 'garden chair', 'garden cart', 'garden shed',
      'house greenhouse', 'cantilever', 'hedge trimmer',
      'bakers rack', 'wheelchair ramp', 'bookshelf',
      'pillow', 'cushion', 'blanket', 'curtain', 'rug', 'carpet',
      'candle', 'vase', 'decoration', 'decor',
      'kitchen', 'cooking', 'baking', 'utensil',
      'storage box', 'organizer', 'shelf', 'furniture',
      'towel', 'bathroom', 'shower', 'soap dispenser',
      'packaging', 'express bag', 'hang tag', 'sticker',
      'card', 'biodegradable', 'delivery bag',
      'egg beater', 'snow shovel', 'shoehorn', 'bidet',
      'door stop', 'display rack', 'deodorant', 'dredging',
      'ceiling light', 'chandelier', 'wall light', 'night light',
      'desk lamp', 'string light', 'led ceiling',
      'floor mat', 'foam sprayer', 'graffiti', 'mural',
      'rubber gasket', 'insulation'], 67),
    (['dress', 'shirt', 'blouse', 'skirt', 'pants', 'jeans', 'jacket',
      'coat', 'sweater', 'hoodie', 'lingerie', 'bra', 'underwear',
      'panties', 'bodysuit', 'swimsuit', 'bikini', 'legging', 'corset',
      'nightgown', 'sleepwear', 'sexy ', 'stocking', 'romper',
      'jumpsuit', 'shapewear', 'bustier', 'thong', 'camisole',
      'negligee', 'outfit', 'clothing', 'costume', 'pajama',
      'nightdress', 'wig', 'gloves', 'swimwear', 'halter',
      'necklace', 'bracelet', 'earring', 'ring ', 'watch ',
      'shoe', 'boot', 'sandal', 'slipper', 'hat ',
      'scarf', 'belt ', 'handbag', 'wallet', 'sunglasses',
      'backpack', 'crossbody bag', 'shoulder bag', 'tote bag',
      'clutch', 'purse', 'loafer', 'heel', 'sneaker',
      'down jacket', 'parka', 'trench', 'blazer', 'cardigan',
      'vest', 'polo', 'tee ', 't-shirt', 'shorts',
      'trouser', 'kimono', 'robe', 'fleece', 'pullover',
      'sweatshirt', 'denim', 'silk ', 'cotton ', 'linen ',
      'wool ', 'knit ', 'embroidered', 'floral', 'striped'], 52),
]


def get_cj_cat_id(raw):
    """Extraire le categoryId CJ depuis raw_data (gère les 2 formats)"""
    cid = raw.get('categoryId') or raw.get('category_id') or ''
    return str(cid).strip() if cid else ''


def get_hierarchy(cj_cat):
    """Retourne (l1_name, l2_name, l3_name)"""
    l3 = cj_cat.name
    c2 = cj_cat
    while c2.parent and c2.level > 2:
        c2 = c2.parent
    l2 = c2.name if c2.level == 2 else None
    c1 = c2
    while c1.parent and c1.level > 1:
        c1 = c1.parent
    l1 = c1.name
    return l1, l2, l3


def get_mps_from_cj(l1, l2, l3):
    """MPS ID via mapping CJ L3 > L2 > L1"""
    if l3 in CJ_L3_OVERRIDES:
        return CJ_L3_OVERRIDES[l3]
    if l2 and l2 in CJ_L2_OVERRIDES:
        return CJ_L2_OVERRIDES[l2]
    if l1 in CJ_L1_TO_MPS:
        return CJ_L1_TO_MPS[l1]
    return None


def get_mps_from_name(name):
    """MPS ID via nom du produit"""
    n = name.lower()
    for keywords, mps_id in NAME_RULES:
        for kw in keywords:
            if kw in n:
                return mps_id
    return None


with app.app_context():
    print("\n" + "="*80)
    print("REMAPPING COMPLET ET FINAL (gère categoryId + category_id)")
    print("="*80 + "\n")
    
    products = Product.query.filter(Product.cj_pid.isnot(None)).all()
    print(f"Total produits CJ: {len(products)}")
    
    stats = {
        'by_cj': 0, 'by_name': 0, 'already_ok': 0,
        'remapped': 0, 'no_raw': 0, 'unresolved': 0
    }
    changes = []
    unresolved = []
    
    for i, p in enumerate(products):
        if not p.cj_raw_data:
            stats['no_raw'] += 1
            continue
        try:
            raw = json.loads(p.cj_raw_data)
        except:
            stats['no_raw'] += 1
            continue
        
        target = None
        method = None
        
        # 1. Essayer par catégorie CJ
        cj_cat_id = get_cj_cat_id(raw)
        if cj_cat_id:
            cj_cat = Category.query.filter_by(cj_category_id=cj_cat_id).first()
            if cj_cat:
                l1, l2, l3 = get_hierarchy(cj_cat)
                target = get_mps_from_cj(l1, l2, l3)
                method = 'CJ'
        
        # 2. Fallback par nom
        if not target:
            target = get_mps_from_name(p.name)
            method = 'NAME'
        
        # 3. Défaut Maison & Jardin
        if not target:
            target = 67
            method = 'DEFAULT'
            unresolved.append(f"  ID:{p.id} | {p.name[:55]} -> Maison (default)")
        
        if target:
            if method == 'CJ':
                stats['by_cj'] += 1
            elif method == 'NAME':
                stats['by_name'] += 1
            else:
                stats['unresolved'] += 1
            
            if p.category_id != target:
                old = db.session.get(Category, p.category_id)
                new = db.session.get(Category, target)
                if len(changes) < 50:
                    changes.append(f"  {p.name[:45]:<45} | {old.name if old else '?':<22} -> {new.name if new else '?'} ({method})")
                p.category_id = target
                stats['remapped'] += 1
            else:
                stats['already_ok'] += 1
        
        if (i + 1) % 5000 == 0:
            print(f"  Traité: {i+1}/{len(products)}")
    
    db.session.commit()
    
    print(f"\n{'='*80}")
    print("RÉSULTATS")
    print(f"{'='*80}\n")
    print(f"  Remappés:      {stats['remapped']}")
    print(f"  Déjà OK:       {stats['already_ok']}")
    print(f"  Par CJ:        {stats['by_cj']}")
    print(f"  Par nom:       {stats['by_name']}")
    print(f"  Par défaut:    {stats['unresolved']}")
    print(f"  Sans raw_data: {stats['no_raw']}")
    
    if changes:
        print(f"\n--- Exemples de changements ({min(len(changes),50)} premiers) ---\n")
        for c in changes:
            print(c)
    
    if unresolved:
        print(f"\n--- Non résolus ({len(unresolved)}) ---")
        for u in unresolved[:20]:
            print(u)
    
    # Distribution finale
    print(f"\n{'='*80}")
    print("DISTRIBUTION FINALE")
    print(f"{'='*80}\n")
    
    from sqlalchemy import func
    dist = Product.query.filter(Product.cj_pid.isnot(None)).with_entities(
        Product.category_id, func.count(Product.id)
    ).group_by(Product.category_id).all()
    
    for cat_id, count in sorted(dist, key=lambda x: x[1], reverse=True):
        cat = db.session.get(Category, cat_id) if cat_id else None
        print(f"  {cat.name if cat else 'AUCUNE':<35} : {count:>6}")
    print(f"\n  {'TOTAL':<35} : {sum(c for _,c in dist):>6}")
