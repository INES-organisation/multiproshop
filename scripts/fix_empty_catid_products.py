"""
Reclasser TOUS les produits dont le categoryId CJ est vide ou non trouvé en BDD.
Utilise les mêmes règles strictes que reclassify_orphans_strict.py.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.product import Product
from models.category import Category
from extensions import db

app = create_app()

RULES = [
    (['pet ', 'dog ', 'cat toy', 'cat bed', 'cat tree', 'bird bath',
      'chicken water', 'poultry', 'cat harness', 'dog kennel',
      'rabbit hutch', 'bird cage', 'pet food', 'pet bowl',
      'pet bed', 'pet collar', 'pet leash', 'aquarium'], 178),
    (['car wash', 'car seat', 'car cover', 'car mat', 'car mirror',
      'car light', 'car charger', 'dashboard', 'windshield', 'bumper',
      'headlight', 'taillight', 'exhaust', 'brake pad', 'suspension',
      'steering', 'wiper', 'rearview mirror', 'rv roof vent',
      'door mirror', 'sunshade', 'grille', 'oil film remover',
      'heat shrink wire connector', 'motorcycle', 'automotive',
      'car roof', 'car phone', 'visor', 'car glass'], 139),
    (['phone case', 'phone holder', 'screen protector', 'power bank',
      'earphone', 'earbud', 'airpod', 'wireless charger', 'phone ring',
      'phone grip', 'phone mount', 'phone cable', 'phone stand',
      'tablet case', 'ipad case', 'sim card', 'phone bracket',
      'data cable', 'charging cable', 'lightning adapter',
      'usb cable', 'type-c', 'otg adapter', 'audio cable',
      'headphone case', 'earphone case', 'headphones soft ca',
      'magnetic wire', 'audio antenna'], 38),
    (['laptop', 'notebook', 'computer', 'keyboard', 'mouse pad',
      'monitor', 'usb hub', 'ssd', 'hard drive', 'printer', 'webcam',
      'desk converter', 'office desk', 'computer desk', 'pc ',
      'cpu', 'gpu', 'ram ', 'router', 'server', 'scanner',
      'laptop stand', 'laptop bracket', 'laptop cooling', 'laptop radiator',
      'notebook bracket', 'notebook cooling', 'notebook radiator',
      'computer bracket', 'computer stand', 'computer cooling',
      'tablet stand', 'tablet bracket', 'tablet holder',
      'laptop bag', 'laptop sleeve', 'laptop case',
      'computer jacket', 'computer bag'], 22),
    (['drone', 'projector', 'camera', 'cctv', 'security cam',
      'gps tracker', 'walkie talkie', 'solar panel',
      'bluetooth speaker', 'bluetooth earbuds', 'bluetooth headset',
      'bluetooth headphone', 'bluetooth helmet', 'bluetooth 5',
      'wireless speaker', 'wireless headphone', 'wireless earphone',
      'wireless ear-hook', 'wireless earbuds',
      'digital camera', 'infrared camera', 'hunting camera',
      'amplifier', 'noise-canceling', 'stereo wireless',
      'translation earbuds', 'smart glasses',
      'karaoke', 'subwoofer', 'ktv', 'speaker set',
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
      'pacifier', 'nursing', 'maternity', 'kids digital camera'], 113),
    (['toy ', 'toys ', 'puzzle', 'plush', 'doll', 'fidget',
      'building block', 'rc car', 'board game', 'action figure',
      'lego', 'children toy'], 126),
    (['fitness', 'gym ', 'yoga ', 'exercise', 'workout', 'treadmill',
      'barbell', 'dumbbell', 'resistance band', 'ab wheel', 'foam roller',
      'pelvic floor', 'spinning fitness', 'calf raise', 'strength training',
      'camping chair', 'camping tent', 'canopy tent', 'hiking',
      'fishing', 'golf ', 'tennis', 'basketball', 'football', 'soccer',
      'cycling', 'bicycle saddle', 'bike ', 'trout bait',
      'beach canopy', 'outdoor solar', 'marathon', 'running vest',
      'boxing', 'bottle cage', 'sports bluetooth',
      'petrol can', 'fuel oil', 'gasoline bucket', 'drag harrow',
      'creeper garage', 'myopia lenses'], 100),
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
      'trash can', 'laundry', 'sewing', 'clock',
      'packaging', 'express bag', 'hang tag', 'sticker',
      'card', 'biodegradable', 'delivery bag',
      'egg beater', 'snow shovel', 'shoehorn', 'bidet',
      'door stop', 'display rack', 'deodorant', 'dredging',
      'ceiling light', 'chandelier', 'wall light', 'night light',
      'desk lamp', 'string light', 'led ceiling',
      'floor mat', 'bathroom mat', 'foam sprayer',
      'graffiti', 'mural', 'colored glass',
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
      'trouser', 'kimono', 'robe',
      'fleece', 'pullover', 'sweatshirt',
      'denim', 'silk ', 'cotton ', 'linen ', 'wool ',
      'knit ', 'embroidered', 'floral', 'striped'], 52),
]


def classify(name):
    n = name.lower()
    for keywords, mps_id in RULES:
        for kw in keywords:
            if kw in n:
                return mps_id, kw
    return None, None


with app.app_context():
    products = Product.query.filter(Product.cj_pid.isnot(None)).all()
    
    # Trouver TOUS les produits dont le categoryId CJ est vide OU non trouvé en BDD
    targets = []
    for p in products:
        is_orphan = False
        if not p.cj_raw_data:
            is_orphan = True
        else:
            try:
                raw = json.loads(p.cj_raw_data)
                cid = str(raw.get('categoryId') or raw.get('category_id') or '')
                if not cid:
                    is_orphan = True
                else:
                    cj = Category.query.filter_by(cj_category_id=cid).first()
                    if not cj:
                        is_orphan = True
            except:
                is_orphan = True
        
        if is_orphan:
            targets.append(p)
    
    print(f"Produits à reclassifier: {len(targets)}\n")
    
    fixed = 0
    ok = 0
    unresolved = []
    
    for p in targets:
        target_id, kw = classify(p.name)
        if target_id:
            if p.category_id != target_id:
                old = db.session.get(Category, p.category_id)
                new = db.session.get(Category, target_id)
                print(f"  FIX {p.name[:45]:<45} | {old.name if old else '?':<22} -> {new.name if new else '?'} ({kw})")
                p.category_id = target_id
                fixed += 1
            else:
                ok += 1
        else:
            old = db.session.get(Category, p.category_id) if p.category_id else None
            unresolved.append(f"  ID:{p.id} | {p.name[:55]} | {old.name if old else '?'}")
    
    db.session.commit()
    
    print(f"\nCorrigés: {fixed}")
    print(f"Déjà OK: {ok}")
    print(f"Non résolus: {len(unresolved)}")
    if unresolved:
        print("\n--- Non résolus ---")
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
