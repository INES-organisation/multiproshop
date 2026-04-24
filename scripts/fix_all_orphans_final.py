"""
Corriger les 99 produits orphelins restants (catégorie CJ non trouvée en BDD).
Utilise categoryName CJ + analyse du nom du produit.
Puis vérification complète par échantillon.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.product import Product
from models.category import Category
from extensions import db

app = create_app()

# Mapping chemin CJ categoryName (L1) -> MPS
CJ_PATH_TO_MPS = {
    "women's clothing": 52,
    "men's clothing": 52,
    "bags & shoes": 52,
    "jewelry & watches": 52,
    "phones & accessories": 38,
    "computer & office": 22,
    "home, garden & furniture": 67,
    "health, beauty & hair": 87,
    "automobiles & motorcycles": 139,
    "sports & outdoors": 100,
    "home improvement": 152,
    "pet supplies": 178,
    "consumer electronics": 1,
    "toys, kids & babies": 126,
    "packing material": 67,
}

# Mots-clés par catégorie MPS pour fallback par nom
KEYWORD_RULES = [
    # Mode & Vêtements (52)
    (['dress', 'shirt', 'blouse', 'skirt', 'pants', 'jeans', 'jacket', 'coat',
      'sweater', 'hoodie', 'lingerie', 'bra ', 'underwear', 'panties', 'bodysuit',
      'swimsuit', 'bikini', 'legging', 'corset', 'nightgown', 'sleepwear',
      'sexy', 'maid uniform', 'belly band', 'sheer', 'lace set', 'stocking',
      'romper', 'jumpsuit', 'shapewear', 'bustier', 'thong', 'camisole',
      'negligee', 'outfit', 'clothing', 'costume', 'pajama', 'nightdress',
      'wig', 'hair extension', 'necklace', 'bracelet', 'earring', 'ring ',
      'watch ', 'shoe', 'boot', 'sandal', 'slipper', 'hat ', 'scarf',
      'glove', 'sock', 'belt ', 'handbag', 'wallet', 'sunglasses',
      'halter', 'crotch', 'embroidery sheer', 'floral embroidery',
      'lace bra', 'mesh bra', 'push-up bra', 'sports bra', 'wireless bra',
      'body chain', 'bodychain'], 52),
    # Santé & Beauté (87)
    (['massage', 'massager', 'fascial gun', 'moisturizing', 'hydrating',
      'skin care', 'beauty', 'cosmetic', 'health', 'cream', 'serum',
      'shampoo', 'lotion', 'nail art', 'hair dryer', 'straightener',
      'curler', 'trimmer', 'shaver', 'essential oil', 'face mask',
      'massage comb', 'heated waist', 'heating waist'], 87),
    # Maison & Jardin (67)
    (['pillow', 'cushion', 'blanket', 'curtain', 'rug', 'carpet',
      'lamp', 'candle', 'vase', 'decoration', 'kitchen', 'cooking',
      'storage box', 'organizer', 'shelf', 'furniture', 'garden',
      'plant', 'flower', 'cleaning', 'towel', 'bathroom', 'shower',
      'packaging', 'express bag', 'hang tag', 'logistics', 'delivery bag',
      'sticker', 'card', 'biodegradable', 'thank you card',
      'customized card'], 67),
    # Jeux & Jouets (126)
    (['toy', 'puzzle', 'plush', 'doll', 'fidget', 'building block',
      'rc car', 'board game', 'action figure'], 126),
    # Téléphonie (38)
    (['phone case', 'phone holder', 'screen protector', 'power bank',
      'earphone', 'earbud', 'bluetooth', 'wireless charger'], 38),
    # Animalerie (178)
    (['pet ', 'dog ', 'cat toy', 'cat bed', 'pet food', 'leash',
      'collar', 'pet bed', 'aquarium'], 178),
    # Bébés (113)
    (['baby', 'infant', 'toddler', 'newborn', 'stroller', 'diaper',
      'pacifier', 'nursing', 'maternity'], 113),
    # Informatique (22)
    (['laptop', 'computer', 'keyboard', 'mouse pad', 'monitor',
      'usb hub', 'ssd', 'hard drive', 'printer', 'webcam'], 22),
    # Auto (139)
    (['car ', 'vehicle', 'motorcycle', 'automotive', 'dashboard',
      'windshield', 'brake', 'engine'], 139),
    # Sports (100)
    (['fitness', 'gym', 'yoga mat', 'camping', 'hiking', 'fishing',
      'cycling', 'golf', 'tennis'], 100),
    # Bricolage (152)
    (['drill', 'saw', 'hammer', 'screwdriver', 'wrench', 'plier',
      'tool set', 'sandpaper', 'paint brush'], 152),
    # Électronique (1)
    (['drone', 'projector', 'camera', 'cctv', 'security cam',
      'gps tracker', 'walkie talkie', 'solar panel'], 1),
]


def guess_mps(name, cj_cat_name):
    """Deviner la catégorie MPS"""
    # 1. Par categoryName CJ
    if cj_cat_name:
        cn_lower = cj_cat_name.lower()
        # Extraire le premier segment (L1)
        l1 = cn_lower.split(' > ')[0].strip()
        for key, mps_id in CJ_PATH_TO_MPS.items():
            if key in l1:
                return mps_id, 'CJ_PATH'
        # Chercher dans le chemin complet
        for key, mps_id in CJ_PATH_TO_MPS.items():
            if key in cn_lower:
                return mps_id, 'CJ_PATH_FULL'
    
    # 2. Par nom du produit
    name_lower = name.lower()
    for keywords, mps_id in KEYWORD_RULES:
        if any(kw in name_lower for kw in keywords):
            return mps_id, 'NAME'
    
    return 67, 'DEFAULT'  # Maison & Jardin par défaut


with app.app_context():
    products = Product.query.filter(Product.cj_pid.isnot(None)).all()
    
    orphans = []
    for p in products:
        if not p.cj_raw_data:
            orphans.append((p, {}))
            continue
        try:
            raw = json.loads(p.cj_raw_data)
        except:
            orphans.append((p, {}))
            continue
        
        cj_cat_id = str(raw.get('categoryId') or raw.get('category_id') or '')
        if not cj_cat_id:
            orphans.append((p, raw))
            continue
        
        cj_cat = Category.query.filter_by(cj_category_id=cj_cat_id).first()
        if not cj_cat:
            orphans.append((p, raw))
    
    print(f"\nOrphelins à traiter: {len(orphans)}\n")
    
    fixed = 0
    for p, raw in orphans:
        cj_cat_name = raw.get('categoryName', '')
        target, method = guess_mps(p.name, cj_cat_name)
        
        old_cat = db.session.get(Category, p.category_id) if p.category_id else None
        new_cat = db.session.get(Category, target)
        
        changed = p.category_id != target
        if changed:
            p.category_id = target
            fixed += 1
        
        status = "FIX" if changed else "OK "
        print(f"  [{status}] {p.name[:50]:<50} | {old_cat.name if old_cat else '?':<20} -> {new_cat.name if new_cat else '?':<20} ({method})")
    
    db.session.commit()
    
    print(f"\nCorrigés: {fixed}/{len(orphans)}")
    
    # Distribution finale complète
    print(f"\n{'='*80}")
    print("DISTRIBUTION FINALE COMPLÈTE")
    print(f"{'='*80}\n")
    
    from sqlalchemy import func
    dist = Product.query.filter(Product.cj_pid.isnot(None)).with_entities(
        Product.category_id, func.count(Product.id)
    ).group_by(Product.category_id).all()
    
    total = 0
    for cat_id, count in sorted(dist, key=lambda x: x[1], reverse=True):
        cat = db.session.get(Category, cat_id) if cat_id else None
        name = cat.name if cat else 'AUCUNE'
        print(f"  {name:<35} : {count:>6}")
        total += 1
    print(f"\n  Total catégories: {total}")
    
    # Échantillon rapide des catégories sensibles
    print(f"\n{'='*80}")
    print("ÉCHANTILLON CATÉGORIES SENSIBLES")
    print(f"{'='*80}")
    
    for mps_id, mps_name in [(1, 'Électronique'), (100, 'Sports'), (152, 'Bricolage')]:
        prods = Product.query.filter_by(category_id=mps_id).filter(
            Product.cj_pid.isnot(None)
        ).all()
        print(f"\n--- {mps_name} ({len(prods)} produits) ---")
        for p in prods:
            print(f"  {p.name[:75]}")
