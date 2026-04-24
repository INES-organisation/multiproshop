"""
Remapping complet 3 niveaux : CJ L3 -> CJ L2 -> CJ L1 -> MPS

Logique de priorité :
1. Si la catégorie CJ L3 a un override spécifique -> utiliser cet override
2. Sinon si la catégorie CJ L2 a un override -> utiliser cet override  
3. Sinon utiliser le mapping par défaut CJ L1 -> MPS

Catégories MPS cibles :
  1  = Électronique & High-Tech
  22 = Informatique
  38 = Téléphonie & Tablettes
  52 = Mode & Vêtements
  67 = Maison & Jardin
  87 = Santé & Beauté
  100 = Sports & Loisirs
  113 = Bébés & Puériculture
  126 = Jeux & Jouets
  139 = Auto & Moto
  152 = Bricolage & Outillage
  178 = Animalerie
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.product import Product
from models.category import Category
from extensions import db

app = create_app()

# ============================================================
# MAPPING CJ L1 (nom) -> MPS ID (défaut)
# ============================================================
CJ_L1_TO_MPS = {
    'Phones & Accessories': 38,       # Téléphonie & Tablettes
    'Computer & Office': 22,          # Informatique
    'Home, Garden & Furniture': 67,   # Maison & Jardin
    "Women's Clothing": 52,           # Mode & Vêtements
    'Jewelry & Watches': 52,          # Mode & Vêtements
    "Men's Clothing": 52,             # Mode & Vêtements
    'Bags & Shoes': 52,               # Mode & Vêtements
    'Health, Beauty & Hair': 87,      # Santé & Beauté
    'Automobiles & Motorcycles': 139, # Auto & Moto
    'Sports & Outdoors': 100,         # Sports & Loisirs
    'Home Improvement': 152,          # Bricolage & Outillage
    'Pet Supplies': 178,              # Animalerie
    'Consumer Electronics': 1,        # Électronique & High-Tech
    'Toys, Kids & Babies': 126,       # Jeux & Jouets (défaut)
}

# ============================================================
# OVERRIDES CJ L2 (nom) -> MPS ID
# ============================================================
CJ_L2_OVERRIDES = {
    # --- Sports & Outdoors ---
    'Swimming': 52,           # Maillots de bain -> Mode & Vêtements
    'Sneakers': 52,           # Chaussures sport -> Mode & Vêtements
    'Sportswear': 52,         # Vêtements sport -> Mode & Vêtements
    
    # --- Home Improvement ---
    'LED Lighting': 67,       # Éclairage LED -> Maison & Jardin
    'Indoor Lighting': 67,    # Éclairage intérieur -> Maison & Jardin
    'Outdoor Lighting': 67,   # Éclairage extérieur -> Maison & Jardin
    'Home Appliances': 67,    # Appareils ménagers -> Maison & Jardin
    
    # --- Toys, Kids & Babies ---
    'Baby Clothing': 113,     # Vêtements bébé -> Bébés & Puériculture
    'Baby & Mother': 113,     # Bébé & Maman -> Bébés & Puériculture
    'Boys Clothing': 52,      # Vêtements garçons -> Mode & Vêtements
    'Girls Clothing': 52,     # Vêtements filles -> Mode & Vêtements
    'Shoes & Bags': 52,       # Chaussures & Sacs enfants -> Mode & Vêtements
    
    # --- Consumer Electronics ---
    'Home Audio & Video': 1,          # Audio/Vidéo -> Électronique
    'Smart Electronics': 1,           # Électronique intelligente -> Électronique
    'Camera & Photo': 1,              # Caméras -> Électronique
    'Video Games': 126,               # Jeux vidéo -> Jeux & Jouets
    'Portable Audio & Video': 1,      # Audio portable -> Électronique
    'Accessories & Parts': 1,         # Accessoires électroniques -> Électronique
    
    # --- Computer & Office ---
    'Office Electronics': 22,         # Électronique bureau -> Informatique
    'Computer Peripherals': 22,       # Périphériques -> Informatique
    'Computer Components': 22,        # Composants -> Informatique
    'Networking': 22,                 # Réseau -> Informatique
    'Tablets & Laptops': 22,          # Tablettes/Laptops -> Informatique
    'Office & School Supplies': 22,   # Fournitures bureau -> Informatique
    'Computer Cleaners': 22,          # Nettoyage PC -> Informatique
    'Desks & Chairs': 67,             # Bureaux & Chaises -> Maison & Jardin
    
    # --- Health, Beauty & Hair ---
    'Skin Care': 87,                  # Soins peau -> Santé & Beauté
    'Beauty Tools': 87,               # Outils beauté -> Santé & Beauté
    'Hair Care & Styling': 87,        # Soins cheveux -> Santé & Beauté
    'Makeup': 87,                     # Maquillage -> Santé & Beauté
    'Nail Art & Tools': 87,           # Ongles -> Santé & Beauté
    'Health Care': 87,                # Santé -> Santé & Beauté
    'Oral Hygiene': 87,               # Hygiène buccale -> Santé & Beauté
    'Fragrances & Deodorants': 87,    # Parfums -> Santé & Beauté
    'Shaving & Hair Removal': 87,     # Rasage -> Santé & Beauté
    
    # --- Bags & Shoes ---
    "Men's Luggage & Bags": 52,       # Sacs hommes -> Mode
    "Women's Luggage & Bags": 52,     # Sacs femmes -> Mode
    'Functional Bags': 52,            # Sacs fonctionnels -> Mode
    "Men's Shoes": 52,                # Chaussures hommes -> Mode
    "Women's Shoes": 52,              # Chaussures femmes -> Mode
    
    # --- Home, Garden & Furniture ---
    'Home Textile': 67,               # Textile maison -> Maison & Jardin
    'Kitchen, Dining & Bar': 67,      # Cuisine -> Maison & Jardin
    'Home Decor': 67,                 # Déco -> Maison & Jardin
    'Bathroom': 67,                   # Salle de bain -> Maison & Jardin
    'Home Storage & Organization': 67, # Rangement -> Maison & Jardin
    'Festive & Party Supplies': 67,   # Fêtes -> Maison & Jardin
    'Garden Supplies': 67,            # Jardin -> Maison & Jardin
    'Furniture': 67,                  # Meubles -> Maison & Jardin
    
    # --- Automobiles & Motorcycles ---
    'Auto Replacement Parts': 139,    # Pièces auto -> Auto & Moto
    'Car Electronics': 139,           # Électronique auto -> Auto & Moto
    'Interior Accessories': 139,      # Accessoires intérieur -> Auto & Moto
    'Exterior Accessories': 139,      # Accessoires extérieur -> Auto & Moto
    'Motorcycle Accessories & Parts': 139, # Moto -> Auto & Moto
    
    # --- Jewelry & Watches ---
    'Fashion Jewelry': 52,            # Bijoux fantaisie -> Mode
    "Women's Watches": 52,            # Montres femmes -> Mode
    "Men's Watches": 52,              # Montres hommes -> Mode
    'Fine Jewelry': 52,               # Bijoux fins -> Mode
    'Wedding & Engagement': 52,       # Mariage -> Mode
}

# ============================================================
# OVERRIDES CJ L3 (nom) -> MPS ID (plus précis)
# ============================================================
CJ_L3_OVERRIDES = {
    # --- Produits qui posent problème spécifiquement ---
    # Sports > Swimming > Bikini Sets -> Mode
    'Bikini Sets': 52,
    'One-Piece Suits': 52,
    'Two-Piece Suits': 52,
    'Cover-Ups': 52,
    
    # Sports > Other Sports Equipment > Camping & Hiking -> Sports
    'Camping & Hiking': 100,
    
    # Home Improvement > Tools -> Bricolage (garder)
    'Hand Tools': 152,
    'Power Tools': 152,
    'Measuring & Leveling': 152,
    'Tool Parts': 152,
    'Home Improvement Materials': 152,
    
    # Home Improvement > LED/Indoor/Outdoor Lighting -> Maison
    'LED Bulbs & Tubes': 67,
    'LED Strips': 67,
    'Ceiling Lights': 67,
    'Pendant Lights': 67,
    'Wall Lamps': 67,
    'Night Lights': 67,
    'Table Lamps': 67,
    'Outdoor Wall Lamps': 67,
    'String Lights': 67,
    'Chandeliers': 67,
    'Flashlights & Torches': 152,  # Lampes torches -> Bricolage
    
    # Computer > Desks & Chairs -> Maison
    'Office & School Supplies': 22,
    
    # Planters / Garden beds dans Home Improvement -> Maison
    'Garden Tools': 67,
    'Watering & Irrigation': 67,
}


def get_hierarchy(cj_cat):
    """Retourne (l1_name, l2_name, l3_name) pour une catégorie CJ"""
    l3_name = cj_cat.name
    
    # Niveau 2
    cat2 = cj_cat
    while cat2.parent and cat2.level > 2:
        cat2 = cat2.parent
    l2_name = cat2.name if cat2.level == 2 else None
    
    # Niveau 1
    cat1 = cat2
    while cat1.parent and cat1.level > 1:
        cat1 = cat1.parent
    l1_name = cat1.name
    
    return l1_name, l2_name, l3_name


def get_mps_id(l1_name, l2_name, l3_name):
    """Déterminer la catégorie MPS avec priorité L3 > L2 > L1"""
    # 1. Override L3
    if l3_name in CJ_L3_OVERRIDES:
        return CJ_L3_OVERRIDES[l3_name], 'L3'
    
    # 2. Override L2
    if l2_name and l2_name in CJ_L2_OVERRIDES:
        return CJ_L2_OVERRIDES[l2_name], 'L2'
    
    # 3. Défaut L1
    if l1_name in CJ_L1_TO_MPS:
        return CJ_L1_TO_MPS[l1_name], 'L1'
    
    return None, None


with app.app_context():
    print("\n" + "="*80)
    print("REMAPPING COMPLET 3 NIVEAUX (L3 > L2 > L1)")
    print("="*80 + "\n")
    
    # Vérifier les catégories MPS
    all_mps_ids = set(CJ_L1_TO_MPS.values()) | set(CJ_L2_OVERRIDES.values()) | set(CJ_L3_OVERRIDES.values())
    for mps_id in sorted(all_mps_ids):
        cat = db.session.get(Category, mps_id)
        if cat:
            print(f"  OK MPS ID {mps_id:3} -> {cat.name}")
        else:
            print(f"  !! MPS ID {mps_id:3} -> NON TROUVÉE !")
            sys.exit(1)
    
    products = Product.query.filter(Product.cj_pid.isnot(None)).all()
    print(f"\nTotal produits CJ: {len(products)}")
    
    stats = {'remapped': 0, 'already_ok': 0, 'no_raw': 0, 'no_cat_id': 0, 'cat_not_found': 0, 'no_mapping': 0}
    by_level = {'L1': 0, 'L2': 0, 'L3': 0}
    mps_dist = {}
    changes = []
    
    for i, p in enumerate(products):
        if not p.cj_raw_data:
            stats['no_raw'] += 1
            continue
        try:
            raw = json.loads(p.cj_raw_data)
        except:
            stats['no_raw'] += 1
            continue
        
        cj_cat_id = str(raw.get('categoryId') or raw.get('category_id') or '')
        if not cj_cat_id:
            stats['no_cat_id'] += 1
            continue
        
        cj_cat = Category.query.filter_by(cj_category_id=cj_cat_id).first()
        if not cj_cat:
            stats['cat_not_found'] += 1
            continue
        
        l1_name, l2_name, l3_name = get_hierarchy(cj_cat)
        target_mps, level = get_mps_id(l1_name, l2_name, l3_name)
        
        if not target_mps:
            stats['no_mapping'] += 1
            continue
        
        by_level[level] += 1
        
        # Compteur distribution
        target_cat = db.session.get(Category, target_mps)
        cat_name = target_cat.name if target_cat else f"ID:{target_mps}"
        mps_dist[cat_name] = mps_dist.get(cat_name, 0) + 1
        
        if p.category_id != target_mps:
            old_cat = db.session.get(Category, p.category_id) if p.category_id else None
            if len(changes) < 30:
                changes.append(f"  {p.name[:50]:<50} | {old_cat.name if old_cat else '?':<25} -> {cat_name} ({level})")
            p.category_id = target_mps
            stats['remapped'] += 1
        else:
            stats['already_ok'] += 1
        
        if (i + 1) % 5000 == 0:
            print(f"  Traité: {i+1}/{len(products)}")
    
    db.session.commit()
    
    # Résultats
    print(f"\n{'='*80}")
    print("RÉSULTATS")
    print(f"{'='*80}\n")
    
    print(f"  Remappés:           {stats['remapped']}")
    print(f"  Déjà corrects:      {stats['already_ok']}")
    print(f"  Sans raw_data:      {stats['no_raw']}")
    print(f"  Sans CJ cat ID:     {stats['no_cat_id']}")
    print(f"  CJ cat non trouvée: {stats['cat_not_found']}")
    print(f"  Pas de mapping:     {stats['no_mapping']}")
    
    print(f"\n  Résolu par L1: {by_level['L1']}")
    print(f"  Résolu par L2: {by_level['L2']}")
    print(f"  Résolu par L3: {by_level['L3']}")
    
    if changes:
        print(f"\n--- Exemples de changements ({len(changes)} premiers) ---\n")
        for c in changes:
            print(c)
    
    print(f"\n{'='*80}")
    print("DISTRIBUTION FINALE")
    print(f"{'='*80}\n")
    
    for name, count in sorted(mps_dist.items(), key=lambda x: x[1], reverse=True):
        print(f"  {name:<35} : {count:>6}")
    total = sum(mps_dist.values())
    print(f"\n  {'TOTAL':<35} : {total:>6}")
