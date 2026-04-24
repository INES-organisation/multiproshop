"""
Correction finale complète :
1. Reclasser "Camping & Hiking" CJ L3 -> Maison & Jardin (la plupart sont gazebos/chaises)
2. Reclasser les vrais produits camping par nom -> Sports
3. Reclasser tous les orphelins restants par nom
4. Vérification complète de toutes les catégories
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.product import Product
from models.category import Category
from extensions import db

app = create_app()

# ============================================================
# ÉTAPE 1 : Reclasser par catégorie CJ L3 (corrections spécifiques)
# ============================================================
# CJ L3 cj_category_id -> nouveau MPS ID
L3_FIXES = {
    # Camping & Hiking -> Maison & Jardin (gazebos, chaises longues, etc.)
    'EA851596-F20F-4AA5-8B3E-E6E7BFCB2E2E': 67,  # Camping & Hiking -> Maison
}

# ============================================================
# ÉTAPE 2 : Mots-clés pour reclasser par nom (post-L3)
# Appliqué à TOUS les produits, pas seulement les orphelins
# ============================================================
# (mots_clés_nom, MPS_ID_cible, catégories_source_à_corriger)
NAME_OVERRIDES = [
    # Vrais produits camping/sports mal classés dans Maison après fix L3
    (['canopy tent', 'camping chair', 'camping stool', 'beach canopy'], 100, [67]),
    # Produits jardin/maison mal classés dans Sports
    (['garden bed', 'raised bed', 'garden chair', 'flower stand', 'plant stand',
      'planter box', 'planter ', 'greenhouse', 'grow house', 'compost bin',
      'patio gazebo', 'porch swing', 'folding lounge', 'chaise lounge',
      'foldable chaise', 'umbrella base', 'pergola', 'wood panel',
      'metal arch', 'topiary', 'cold frame', 'crop cage',
      'garden cart', 'garden shed', 'hedge trimmer', 'bakers rack',
      'wheelchair ramp', 'house greenhouse', 'cantilever',
      'metal planter', 'garden bed', 'garden compost',
      'beach set', 'hammock with iron stand'], 67, [100, 152]),
    # Produits électronique/speakers mal classés
    (['bluetooth speaker', 'karaoke', 'subwoofer', 'ktv speaker',
      'digital camera', 'hunting camera', 'infrared camera'], 1, [67, 100]),
    # Produits santé mal classés
    (['massage pillow', 'shiatsu', 'led photon skin', 'therapeutic lumbar',
      'sweat-inducing', 'fascial gun'], 87, [67, 52, 100]),
]


with app.app_context():
    print("\n" + "="*80)
    print("CORRECTION FINALE COMPLÈTE")
    print("="*80)
    
    # --- ÉTAPE 1 : Fix par CJ L3 ---
    print("\n--- Étape 1 : Corrections par CJ L3 ---\n")
    
    products = Product.query.filter(Product.cj_pid.isnot(None)).all()
    fix1 = 0
    
    for p in products:
        if not p.cj_raw_data:
            continue
        try:
            raw = json.loads(p.cj_raw_data)
        except:
            continue
        
        cj_cat_id = str(raw.get('categoryId') or '')
        if not cj_cat_id:
            continue
        
        cj_cat = Category.query.filter_by(cj_category_id=cj_cat_id).first()
        if not cj_cat:
            continue
        
        # Vérifier L3 direct
        if cj_cat.cj_category_id in L3_FIXES:
            target = L3_FIXES[cj_cat.cj_category_id]
            if p.category_id != target:
                old = db.session.get(Category, p.category_id)
                new = db.session.get(Category, target)
                print(f"  L3 FIX: {p.name[:50]:<50} | {old.name if old else '?'} -> {new.name if new else '?'}")
                p.category_id = target
                fix1 += 1
        
        # Vérifier L2 (parent de la catégorie L3)
        if cj_cat.parent and cj_cat.parent.cj_category_id in L3_FIXES:
            target = L3_FIXES[cj_cat.parent.cj_category_id]
            if p.category_id != target:
                old = db.session.get(Category, p.category_id)
                new = db.session.get(Category, target)
                print(f"  L2 FIX: {p.name[:50]:<50} | {old.name if old else '?'} -> {new.name if new else '?'}")
                p.category_id = target
                fix1 += 1
    
    db.session.commit()
    print(f"\n  Corrigés étape 1: {fix1}")
    
    # --- ÉTAPE 2 : Fix par nom ---
    print("\n--- Étape 2 : Corrections par nom ---\n")
    
    fix2 = 0
    for keywords, target_mps, source_mps_ids in NAME_OVERRIDES:
        for p in products:
            if p.category_id not in source_mps_ids:
                continue
            name_lower = p.name.lower()
            matched = any(kw in name_lower for kw in keywords)
            if matched and p.category_id != target_mps:
                old = db.session.get(Category, p.category_id)
                new = db.session.get(Category, target_mps)
                print(f"  NAME FIX: {p.name[:50]:<50} | {old.name if old else '?'} -> {new.name if new else '?'}")
                p.category_id = target_mps
                fix2 += 1
    
    db.session.commit()
    print(f"\n  Corrigés étape 2: {fix2}")
    
    # --- ÉTAPE 3 : Fix orphelins restants ---
    print("\n--- Étape 3 : Orphelins restants ---\n")
    
    orphan_rules = [
        (['garden', 'planter', 'greenhouse', 'flower stand', 'plant stand',
          'gazebo', 'porch swing', 'lounge chair', 'chaise lounge',
          'pergola', 'hammock', 'bookshelf', 'pillow', 'cushion',
          'blanket', 'curtain', 'lamp', 'candle', 'vase', 'decoration',
          'kitchen', 'storage', 'organizer', 'shelf', 'furniture',
          'towel', 'bathroom', 'shower', 'packaging', 'express bag',
          'hang tag', 'sticker', 'card', 'biodegradable', 'egg beater',
          'snow shovel', 'shoehorn', 'bidet', 'door stop', 'display rack',
          'wood panel', 'wheelchair ramp', 'garden chair', 'garden cart',
          'garden shed', 'metal arch', 'topiary', 'raised bed',
          'compost', 'beach set', 'folding lounge'], 67),
        (['dress', 'shirt', 'blouse', 'skirt', 'pants', 'jeans', 'jacket',
          'coat', 'sweater', 'hoodie', 'lingerie', 'bra', 'underwear',
          'panties', 'bodysuit', 'swimsuit', 'bikini', 'legging', 'corset',
          'nightgown', 'sleepwear', 'sexy', 'stocking', 'romper', 'jumpsuit',
          'shapewear', 'bustier', 'thong', 'camisole', 'negligee', 'outfit',
          'clothing', 'costume', 'pajama', 'nightdress', 'wig', 'gloves',
          'swimwear', 'halter', 'lace bra', 'mesh bra', 'push-up',
          'sports bra', 'wireless bra', 'body chain', 'pedometer watch',
          'safety gloves'], 52),
        (['massage', 'massager', 'fascial gun', 'moisturizing', 'hydrating',
          'skin care', 'beauty', 'infrared', 'therapeutic', 'lumbar support',
          'photon skin', 'rejuvenation', 'supplement', 'vitamin',
          'blood pressure', 'toothbrush', 'scrubber'], 87),
        (['fitness', 'gym', 'yoga', 'exercise', 'workout', 'treadmill',
          'barbell', 'dumbbell', 'resistance band', 'ab wheel', 'foam roller',
          'camping', 'hiking', 'fishing', 'golf', 'tennis', 'cycling',
          'bicycle', 'trout bait', 'petrol can', 'fuel oil', 'gasoline',
          'drag harrow', 'creeper garage', 'canopy tent'], 100),
        (['bluetooth speaker', 'bluetooth earbuds', 'bluetooth headset',
          'digital camera', 'hunting camera', 'karaoke', 'subwoofer',
          'amplifier', 'noise-canceling', 'drone', 'projector'], 1),
        (['phone case', 'phone holder', 'screen protector', 'power bank',
          'earphone', 'earbud', 'wireless charger'], 38),
        (['pet ', 'dog ', 'cat toy', 'bird bath', 'chicken water',
          'poultry', 'cat harness', 'dog kennel'], 178),
        (['baby', 'infant', 'toddler', 'newborn', 'stroller', 'diaper',
          'pacifier', 'nursing', 'maternity'], 113),
        (['toy', 'puzzle', 'plush', 'doll', 'fidget', 'building block'], 126),
        (['flashlight', 'torch', 'tool set', 'combination tool',
          'leaf blower', 'crimping', 'airbrush', 'wrench', 'shovel'], 152),
        (['laptop', 'computer', 'keyboard', 'monitor', 'usb hub',
          'printer', 'webcam', 'desk converter'], 22),
        (['car ', 'vehicle', 'motorcycle', 'brake', 'engine',
          'dashboard', 'windshield', 'car wash'], 139),
    ]
    
    fix3 = 0
    still_orphan = []
    
    for p in products:
        if not p.cj_raw_data:
            is_orphan = True
        else:
            try:
                raw = json.loads(p.cj_raw_data)
                cj_cat_id = str(raw.get('categoryId') or '')
                if not cj_cat_id:
                    is_orphan = True
                else:
                    cj_cat = Category.query.filter_by(cj_category_id=cj_cat_id).first()
                    is_orphan = cj_cat is None
            except:
                is_orphan = True
        
        if not is_orphan:
            continue
        
        name_lower = p.name.lower()
        target = None
        for keywords, mps_id in orphan_rules:
            if any(kw in name_lower for kw in keywords):
                target = mps_id
                break
        
        if target and p.category_id != target:
            old = db.session.get(Category, p.category_id)
            new = db.session.get(Category, target)
            print(f"  ORPHAN FIX: {p.name[:45]:<45} | {old.name if old else '?'} -> {new.name if new else '?'}")
            p.category_id = target
            fix3 += 1
        elif not target:
            old = db.session.get(Category, p.category_id) if p.category_id else None
            still_orphan.append(f"  ID:{p.id} | {p.name[:55]} | {old.name if old else '?'}")
    
    db.session.commit()
    print(f"\n  Corrigés étape 3: {fix3}")
    
    if still_orphan:
        print(f"\n  Orphelins non résolus ({len(still_orphan)}):")
        for s in still_orphan:
            print(f"    {s}")
    
    # --- DISTRIBUTION FINALE ---
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
    
    # --- VÉRIFICATION PAR CATÉGORIE ---
    print(f"\n{'='*80}")
    print("VÉRIFICATION PAR CATÉGORIE (échantillon)")
    print(f"{'='*80}")
    
    for mps_id, mps_name in [(100, 'Sports'), (152, 'Bricolage'), (1, 'Électronique'), (67, 'Maison (10 premiers)')]:
        prods = Product.query.filter_by(category_id=mps_id).filter(
            Product.cj_pid.isnot(None)
        ).limit(10).all()
        total = Product.query.filter_by(category_id=mps_id).filter(Product.cj_pid.isnot(None)).count()
        print(f"\n--- {mps_name} ({total} produits) ---")
        for p in prods:
            print(f"  {p.name[:75]}")
