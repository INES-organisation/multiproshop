"""
Reclassifier TOUS les produits orphelins (categoryId CJ non trouvé en BDD)
en analysant leur nom de manière exhaustive.
Couvre toutes les catégories MPS, pas seulement Sports.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.product import Product
from models.category import Category
from extensions import db

app = create_app()

# Règles de classification par mots-clés (ordre = priorité)
# Chaque règle: (mots_clés, MPS_ID, MPS_nom)
RULES = [
    # --- Maison & Jardin (67) --- priorité haute pour garden/planter/greenhouse
    (['garden bed', 'raised bed', 'garden chair', 'flower stand', 'plant stand',
      'planter box', 'planter ', 'greenhouse', 'grow house', 'compost bin',
      'patio gazebo', 'porch swing', 'lounge chair', 'chaise lounge',
      'umbrella base', 'pergola', 'hammock', 'wood panels for wall',
      'garden cart', 'garden compost', 'hedge trimmer', 'bakers rack',
      'garden shed', 'metal arch', 'topiary', 'cold frame',
      'crop cage', 'plant protection', 'cantilever umbrella',
      'wheelchair ramp', 'beach set', 'folding lounge', 'garden bed',
      'metal planter', 'plastic planter', 'tall planter',
      'pillow', 'cushion', 'blanket', 'curtain', 'rug', 'carpet',
      'lamp ', 'candle', 'vase', 'decoration', 'decor',
      'kitchen', 'cooking', 'baking', 'utensil',
      'storage box', 'organizer', 'shelf', 'furniture',
      'cleaning', 'towel', 'bathroom', 'shower',
      'packaging', 'express bag', 'hang tag', 'logistics',
      'delivery bag', 'sticker', 'customized card', 'thank you card',
      'biodegradable', 'bookshelf', 'karaoke', 'subwoofer',
      'air cooler', 'air conditioner fan', 'humidifier',
      'desk lamp', 'night light', 'chandelier', 'ceiling light',
      'wall light', 'led strip', 'string light',
      'soap dispenser', 'trash can', 'laundry', 'iron ',
      'sewing', 'clock', 'thermometer indoor',
      'egg beater', 'snow shovel', 'shoehorn', 'bidet',
      'door stop', 'display rack'], 67, 'Maison & Jardin'),

    # --- Mode & Vêtements (52) ---
    (['dress', 'shirt', 'blouse', 'skirt', 'pants', 'jeans', 'jacket', 'coat',
      'sweater', 'hoodie', 'lingerie', 'bra ', ' bra', 'underwear', 'panties',
      'bodysuit', 'swimsuit', 'bikini', 'legging', 'corset', 'nightgown',
      'sleepwear', 'sexy ', 'maid uniform', 'belly band', 'sheer ',
      'lace set', 'stocking', 'romper', 'jumpsuit', 'shapewear',
      'bustier', 'thong', 'camisole', 'negligee', 'outfit',
      'clothing', 'costume', 'pajama', 'nightdress',
      'wig', 'hair extension', 'necklace', 'bracelet', 'earring',
      'ring ', 'watch ', 'shoe', 'boot', 'sandal', 'slipper',
      'hat ', 'scarf', 'glove', 'sock', 'belt ',
      'handbag', 'wallet', 'sunglasses', 'halter',
      'crotch', 'push-up', 'sports bra', 'wireless bra',
      'body chain', 'leopard', 'lace bra', 'mesh bra',
      'safety gloves', 'work gloves', 'pedometer watch',
      'swimwear', 'coverup'], 52, 'Mode & Vêtements'),

    # --- Santé & Beauté (87) ---
    (['massage', 'massager', 'fascial gun', 'moisturizing', 'hydrating',
      'skin care', 'beauty', 'cosmetic', 'cream', 'serum',
      'shampoo', 'lotion', 'nail art', 'hair dryer', 'straightener',
      'curler', 'trimmer', 'shaver', 'essential oil', 'face mask',
      'massage comb', 'heated waist', 'heating waist',
      'blood pressure', 'thermometer', 'health care',
      'supplement', 'vitamin', 'capsule', 'toothbrush',
      'scrubber', 'bath heater'], 87, 'Santé & Beauté'),

    # --- Sports & Loisirs (100) ---
    (['fitness', 'gym ', 'yoga ', 'exercise', 'workout', 'running',
      'cycling', 'bicycle', 'bike ', 'camping chair', 'camping ',
      'hiking', 'fishing', 'golf ', 'tennis', 'basketball',
      'football', 'soccer', 'skateboard', 'treadmill',
      'barbell', 'dumbbell', 'resistance band', 'ab wheel',
      'foam roller', 'pelvic floor', 'spinning fitness',
      'calf raise', 'strength training', 'beach canopy',
      'trout bait', 'drag harrow', 'petrol can', 'fuel oil',
      'gasoline bucket', 'creeper garage'], 100, 'Sports & Loisirs'),

    # --- Téléphonie (38) ---
    (['phone case', 'phone holder', 'screen protector', 'power bank',
      'earphone', 'earbud', 'airpod', 'wireless charger',
      'phone ring', 'phone grip', 'phone mount', 'phone cable',
      'tablet case', 'ipad case'], 38, 'Téléphonie & Tablettes'),

    # --- Informatique (22) ---
    (['laptop', 'computer', 'keyboard', 'mouse pad', 'monitor',
      'usb hub', 'ssd', 'hard drive', 'printer', 'webcam',
      'desk converter', 'office desk', 'computer desk'], 22, 'Informatique'),

    # --- Électronique (1) ---
    (['drone', 'projector', 'camera', 'cctv', 'security cam',
      'gps tracker', 'walkie talkie', 'solar panel',
      'bluetooth speaker', 'bluetooth earbuds', 'bluetooth headset',
      'bluetooth headphone', 'wireless speaker', 'wireless headphone',
      'digital camera', 'infrared camera', 'hunting camera',
      'amplifier board', 'noise-canceling', 'stereo wireless',
      'ear-hook', 'translation earbuds', 'protective case for hero',
      'telescoping rod', 'laser level'], 1, 'Électronique & High-Tech'),

    # --- Auto & Moto (139) ---
    (['car ', 'vehicle', 'motorcycle', 'automotive', 'dashboard',
      'windshield', 'brake', 'engine', 'exhaust', 'bumper',
      'headlight', 'taillight', 'car wash', 'car seat',
      'car cover', 'car mat', 'foldable garage'], 139, 'Auto & Moto'),

    # --- Animalerie (178) ---
    (['pet ', 'dog ', 'cat toy', 'cat bed', 'cat tree',
      'pet food', 'leash', ' collar', 'pet bed',
      'aquarium', 'bird bath', 'chicken water',
      'cat harness', 'dog kennel', 'rabbit hutch',
      'bird cage', 'cat feather', 'electric car with wire-feather toy for cats'], 178, 'Animalerie'),

    # --- Bébés & Puériculture (113) ---
    (['baby', 'infant', 'toddler', 'newborn', 'stroller', 'diaper',
      'pacifier', 'nursing', 'maternity', 'kids digital camera'], 113, 'Bébés & Puériculture'),

    # --- Jeux & Jouets (126) ---
    (['toy', 'puzzle', 'plush', 'doll', 'fidget', 'building block',
      'rc car', 'board game', 'action figure', 'lego'], 126, 'Jeux & Jouets'),

    # --- Bricolage (152) ---
    (['drill', 'saw ', 'hammer', 'screwdriver', 'wrench', 'plier',
      'tool set', 'sandpaper', 'paint brush', 'crimping',
      'flashlight', 'torch ', 'airbrush', 'tool case',
      'combination tool', 'cordless leaf blower',
      'piercing jewelry diamond setting tool',
      'stainless steel shovel'], 152, 'Bricolage & Outillage'),
]


def classify_by_name(name):
    """Classifier un produit par son nom"""
    name_lower = name.lower()
    for keywords, mps_id, mps_name in RULES:
        for kw in keywords:
            if kw in name_lower:
                return mps_id, mps_name, kw
    return None, None, None


with app.app_context():
    # Trouver TOUS les orphelins
    products = Product.query.filter(Product.cj_pid.isnot(None)).all()
    
    orphans = []
    for p in products:
        if not p.cj_raw_data:
            orphans.append(p)
            continue
        try:
            raw = json.loads(p.cj_raw_data)
        except:
            orphans.append(p)
            continue
        
        cj_cat_id = str(raw.get('categoryId') or raw.get('category_id') or '')
        if not cj_cat_id:
            orphans.append(p)
            continue
        
        cj_cat = Category.query.filter_by(cj_category_id=cj_cat_id).first()
        if not cj_cat:
            orphans.append(p)
    
    print(f"Orphelins à reclassifier: {len(orphans)}\n")
    
    fixed = 0
    unchanged = 0
    unresolved = []
    
    for p in orphans:
        target_id, target_name, matched_kw = classify_by_name(p.name)
        
        if target_id:
            if p.category_id != target_id:
                old_cat = db.session.get(Category, p.category_id) if p.category_id else None
                print(f"  FIX {p.name[:50]:<50} | {old_cat.name if old_cat else '?':<22} -> {target_name} (kw: {matched_kw})")
                p.category_id = target_id
                fixed += 1
            else:
                unchanged += 1
        else:
            old_cat = db.session.get(Category, p.category_id) if p.category_id else None
            unresolved.append(f"  ??? {p.name[:55]:<55} | Actuel: {old_cat.name if old_cat else '?'}")
    
    db.session.commit()
    
    print(f"\nCorrigés: {fixed}")
    print(f"Déjà corrects: {unchanged}")
    print(f"Non résolus: {len(unresolved)}")
    
    if unresolved:
        print(f"\n--- Non résolus ---")
        for u in unresolved:
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
        name = cat.name if cat else 'AUCUNE'
        print(f"  {name:<35} : {count:>6}")
    
    total = sum(c for _, c in dist)
    print(f"\n  {'TOTAL':<35} : {total:>6}")
