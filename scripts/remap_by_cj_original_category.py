"""
Remapper les produits CJ vers les catégories MPS en utilisant
la catégorie CJ ORIGINALE du produit (depuis cj_raw_data).

Mapping CJ niveau 1 -> MPS :
  Phones & Accessories      -> Téléphonie & Tablettes (38)
  Computer & Office         -> Informatique (22)
  Home, Garden & Furniture  -> Maison & Jardin (67)
  Women's Clothing          -> Mode & Vêtements (52)
  Jewelry & Watches         -> Mode & Vêtements (52)
  Men's Clothing            -> Mode & Vêtements (52)
  Bags & Shoes              -> Mode & Vêtements (52)
  Health, Beauty & Hair     -> Santé & Beauté (87)
  Automobiles & Motorcycles -> Auto & Moto (139)
  Sports & Outdoors         -> Sports & Loisirs (100)
  Home Improvement          -> Bricolage & Outillage (152)
  Pet Supplies              -> Animalerie (178)
  Consumer Electronics      -> Électronique & High-Tech (1)
  
  Toys, Kids & Babies (séparé par sous-catégorie CJ niveau 2) :
    Toys & Hobbies          -> Jeux & Jouets (126)
    Baby Clothing           -> Bébés & Puériculture (113)
    Baby & Mother           -> Bébés & Puériculture (113)
    Boys Clothing           -> Mode & Vêtements (52)
    Girls Clothing          -> Mode & Vêtements (52)
    Shoes & Bags            -> Mode & Vêtements (52)
"""
import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.product import Product
from models.category import Category
from extensions import db

app = create_app()

# Mapping CJ niveau 1 name -> MPS category ID
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
}

# Mapping spécial pour Toys, Kids & Babies (par sous-catégorie CJ niveau 2)
TOYS_L2_TO_MPS = {
    'Toys & Hobbies': 126,     # Jeux & Jouets
    'Baby Clothing': 113,      # Bébés & Puériculture
    'Baby & Mother': 113,      # Bébés & Puériculture
    'Boys Clothing': 52,       # Mode & Vêtements
    'Girls Clothing': 52,      # Mode & Vêtements
    'Shoes & Bags': 52,        # Mode & Vêtements
}

# Fallback pour Toys, Kids & Babies si sous-catégorie inconnue
TOYS_DEFAULT_MPS = 126  # Jeux & Jouets


def get_cj_level1_name(cj_cat):
    """Remonter au niveau 1 d'une catégorie CJ"""
    current = cj_cat
    while current.parent and current.level > 1:
        current = current.parent
    return current.name


def get_cj_level2_name(cj_cat):
    """Remonter au niveau 2 d'une catégorie CJ"""
    current = cj_cat
    while current.parent and current.level > 2:
        current = current.parent
    return current.name if current.level == 2 else None


def get_mps_category_id(cj_cat):
    """Déterminer la catégorie MPS à partir de la catégorie CJ"""
    l1_name = get_cj_level1_name(cj_cat)
    
    # Cas spécial : Toys, Kids & Babies -> séparer par sous-catégorie
    if l1_name == 'Toys, Kids & Babies':
        l2_name = get_cj_level2_name(cj_cat)
        if l2_name and l2_name in TOYS_L2_TO_MPS:
            return TOYS_L2_TO_MPS[l2_name]
        return TOYS_DEFAULT_MPS
    
    # Cas normal : mapping direct par niveau 1
    if l1_name in CJ_L1_TO_MPS:
        return CJ_L1_TO_MPS[l1_name]
    
    return None


with app.app_context():
    print("\n" + "="*80)
    print("REMAPPING PRODUITS CJ -> MPS (basé sur catégorie CJ originale)")
    print("="*80 + "\n")
    
    # Vérifier que les catégories MPS existent
    all_mps_ids = set(CJ_L1_TO_MPS.values()) | set(TOYS_L2_TO_MPS.values())
    for mps_id in all_mps_ids:
        cat = Category.query.get(mps_id)
        if cat:
            print(f"  ✅ MPS ID {mps_id:3} -> {cat.name}")
        else:
            print(f"  ❌ MPS ID {mps_id:3} -> NON TROUVÉE !")
            sys.exit(1)
    
    print()
    
    # Récupérer tous les produits CJ
    products = Product.query.filter(Product.cj_pid.isnot(None)).all()
    print(f"Total produits CJ: {len(products)}")
    
    # Statistiques
    stats = {
        'remapped': 0,
        'already_correct': 0,
        'no_raw_data': 0,
        'no_cj_cat_id': 0,
        'cj_cat_not_found': 0,
        'no_mapping': 0,
    }
    
    mps_distribution = {}  # MPS cat name -> count
    
    for i, product in enumerate(products):
        if not product.cj_raw_data:
            stats['no_raw_data'] += 1
            continue
        
        try:
            raw = json.loads(product.cj_raw_data)
        except (json.JSONDecodeError, TypeError):
            stats['no_raw_data'] += 1
            continue
        
        cj_cat_id = str(raw.get('category_id') or raw.get('categoryId') or '')
        if not cj_cat_id:
            stats['no_cj_cat_id'] += 1
            continue
        
        # Trouver la catégorie CJ en BDD
        cj_cat = Category.query.filter_by(cj_category_id=cj_cat_id).first()
        if not cj_cat:
            stats['cj_cat_not_found'] += 1
            continue
        
        # Déterminer la catégorie MPS cible
        target_mps_id = get_mps_category_id(cj_cat)
        if not target_mps_id:
            stats['no_mapping'] += 1
            continue
        
        # Mettre à jour si nécessaire
        if product.category_id != target_mps_id:
            product.category_id = target_mps_id
            stats['remapped'] += 1
        else:
            stats['already_correct'] += 1
        
        # Compteur distribution
        target_cat = Category.query.get(target_mps_id)
        cat_name = target_cat.name if target_cat else f"ID:{target_mps_id}"
        mps_distribution[cat_name] = mps_distribution.get(cat_name, 0) + 1
        
        # Progression
        if (i + 1) % 2000 == 0:
            print(f"  Traité: {i+1}/{len(products)}")
    
    # Sauvegarder
    db.session.commit()
    
    # Résultats
    print("\n" + "="*80)
    print("RÉSULTATS DU REMAPPING")
    print("="*80 + "\n")
    
    print(f"  Remappés:           {stats['remapped']}")
    print(f"  Déjà corrects:      {stats['already_correct']}")
    print(f"  Sans raw_data:      {stats['no_raw_data']}")
    print(f"  Sans CJ cat ID:     {stats['no_cj_cat_id']}")
    print(f"  CJ cat non trouvée: {stats['cj_cat_not_found']}")
    print(f"  Pas de mapping:     {stats['no_mapping']}")
    
    print("\n" + "="*80)
    print("DISTRIBUTION FINALE PAR CATÉGORIE MPS")
    print("="*80 + "\n")
    
    sorted_dist = sorted(mps_distribution.items(), key=lambda x: x[1], reverse=True)
    for name, count in sorted_dist:
        print(f"  {name:<35} : {count:>6} produits")
    
    total = sum(c for _, c in sorted_dist)
    print(f"\n  {'TOTAL':<35} : {total:>6} produits")
    
    print("\n✅ Remapping terminé !")
