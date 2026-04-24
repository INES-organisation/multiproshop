"""
Correction finale : reclasser les produits mal placés dans toutes les catégories.
Analyse nom par nom pour TOUS les produits orphelins (sans catégorie CJ en BDD).
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.product import Product
from models.category import Category
from extensions import db

app = create_app()

# Mots-clés Maison & Jardin
MAISON_KW = [
    'garden', 'planter', 'greenhouse', 'grow house', 'flower stand', 'plant stand',
    'gazebo', 'porch swing', 'lounge chair', 'chaise lounge', 'folding lounge',
    'umbrella base', 'pergola', 'wood panel', 'metal arch', 'topiary',
    'cold frame', 'crop cage', 'raised bed', 'compost', 'hammock',
    'beach set', 'garden chair', 'garden cart', 'garden shed',
    'garden bed', 'house greenhouse', 'cantilever', 'hedge trimmer',
    'bakers rack', 'wheelchair ramp', 'bookshelf', 'led photon skin',
    'pillow', 'massage pillow',
]

# Mots-clés Sports & Loisirs (vrais produits sport)
SPORTS_KW = [
    'fitness', 'gym', 'yoga', 'exercise', 'workout', 'treadmill',
    'barbell', 'dumbbell', 'resistance band', 'ab wheel', 'foam roller',
    'pelvic floor', 'spinning', 'calf raise', 'strength training',
    'camping chair', 'camping ', 'hiking', 'fishing', 'golf ',
    'tennis', 'basketball', 'football', 'soccer', 'cycling',
    'bicycle', 'bike saddle', 'trout bait', 'beach canopy',
    'drag harrow', 'petrol can', 'fuel oil', 'gasoline bucket',
    'creeper garage', 'myopia lenses',
]

# Mots-clés Mode
MODE_KW = [
    'dress', 'shirt', 'blouse', 'skirt', 'pants', 'jeans', 'jacket', 'coat',
    'sweater', 'hoodie', 'lingerie', 'bra', 'underwear', 'panties', 'bodysuit',
    'swimsuit', 'bikini', 'legging', 'corset', 'nightgown', 'sleepwear',
    'sexy ', 'stocking', 'romper', 'jumpsuit', 'shapewear', 'bustier',
    'thong', 'camisole', 'negligee', 'outfit', 'clothing', 'costume',
    'pajama', 'nightdress', 'wig', 'gloves', 'safety gloves',
    'pedometer watch', 'swimwear',
]

# Mots-clés Santé
SANTE_KW = [
    'massage', 'massager', 'fascial gun', 'moisturizing', 'hydrating',
    'skin care', 'beauty', 'cosmetic', 'infrared', 'therapeutic',
    'lumbar support', 'sweat-inducing', 'photon skin', 'rejuvenation',
]

# Mots-clés Électronique
ELEC_KW = [
    'bluetooth speaker', 'bluetooth earbuds', 'bluetooth headset',
    'bluetooth headphone', 'wireless speaker', 'wireless headphone',
    'digital camera', 'infrared camera', 'hunting camera',
    'amplifier', 'noise-canceling', 'stereo wireless',
    'ear-hook', 'translation earbuds', 'protective case for hero',
    'telescoping rod', 'laser level', 'karaoke', 'subwoofer',
    'ktv', 'speaker set',
]

# Mots-clés Animalerie
ANIMAL_KW = [
    'pet ', 'dog ', 'cat toy', 'cat bed', 'cat tree',
    'bird bath', 'chicken water', 'cat harness', 'dog kennel',
    'wire-feather toy for cats', 'poultry',
]

# Mots-clés Bricolage
BRICO_KW = [
    'flashlight', 'torch', 'tool set', 'combination tool',
    'leaf blower', 'crimping', 'airbrush', 'wrench',
    'shovel', 'rgb color portable lamp',
]


def classify(name):
    """Classifier un produit par son nom avec priorité"""
    n = name.lower()
    
    # Priorité 1 : Animalerie (très spécifique)
    if any(kw in n for kw in ANIMAL_KW):
        return 178, 'Animalerie'
    
    # Priorité 2 : Santé (spécifique)
    if any(kw in n for kw in SANTE_KW):
        return 87, 'Santé & Beauté'
    
    # Priorité 3 : Mode (avant Maison car "pillow" peut matcher faux)
    if any(kw in n for kw in MODE_KW):
        return 52, 'Mode & Vêtements'
    
    # Priorité 4 : Maison & Jardin
    if any(kw in n for kw in MAISON_KW):
        return 67, 'Maison & Jardin'
    
    # Priorité 5 : Sports
    if any(kw in n for kw in SPORTS_KW):
        return 100, 'Sports & Loisirs'
    
    # Priorité 6 : Électronique
    if any(kw in n for kw in ELEC_KW):
        return 1, 'Électronique'
    
    # Priorité 7 : Bricolage
    if any(kw in n for kw in BRICO_KW):
        return 152, 'Bricolage'
    
    return None, None


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
    
    print(f"Orphelins: {len(orphans)}\n")
    
    fixed = 0
    ok = 0
    unresolved = []
    
    for p in orphans:
        target_id, target_name = classify(p.name)
        
        if target_id and p.category_id != target_id:
            old_cat = db.session.get(Category, p.category_id) if p.category_id else None
            print(f"  FIX {p.name[:50]:<50} | {old_cat.name if old_cat else '?':<22} -> {target_name}")
            p.category_id = target_id
            fixed += 1
        elif target_id:
            ok += 1
        else:
            old_cat = db.session.get(Category, p.category_id) if p.category_id else None
            unresolved.append((p, old_cat))
    
    db.session.commit()
    
    print(f"\nCorrigés: {fixed}")
    print(f"Déjà OK: {ok}")
    print(f"Non résolus: {len(unresolved)}")
    
    if unresolved:
        print("\n--- Non résolus ---")
        for p, cat in unresolved:
            print(f"  ID:{p.id} | {p.name[:60]} | Actuel: {cat.name if cat else '?'}")
    
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
    
    # Vérification Sports
    print(f"\n--- Sports & Loisirs (vérification) ---")
    sports = Product.query.filter_by(category_id=100).filter(Product.cj_pid.isnot(None)).all()
    for p in sports:
        print(f"  {p.name[:75]}")
