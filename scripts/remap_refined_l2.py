"""
Remapping affiné au niveau 2 CJ.
Corrige les sous-catégories CJ qui sont mal mappées par le mapping niveau 1.

Corrections :
- Sports & Outdoors > Swimming -> Mode & Vêtements (52) au lieu de Sports (100)
- Sports & Outdoors > Sneakers -> Mode & Vêtements (52) au lieu de Sports (100)
- Sports & Outdoors > Sportswear -> Mode & Vêtements (52) au lieu de Sports (100)
- Home Improvement > LED Lighting -> Maison & Jardin (67) au lieu de Bricolage (152)
- Home Improvement > Indoor Lighting -> Maison & Jardin (67) au lieu de Bricolage (152)
- Home Improvement > Outdoor Lighting -> Maison & Jardin (67) au lieu de Bricolage (152)
- Home Improvement > Home Appliances -> Maison & Jardin (67) au lieu de Bricolage (152)
+ Correction des orphelins restants par nom de produit
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

# Mapping affiné : CJ L2 cj_category_id -> MPS ID (override du mapping L1)
CJ_L2_OVERRIDES = {
    # Sports & Outdoors > Swimming -> Mode & Vêtements
    '4B36F14A-6894-4047-8845-56CAFCF9A914': 52,
    # Sports & Outdoors > Sneakers -> Mode & Vêtements
    '1E2633D4-2F96-4E2A-ABF7-BCBF3DFEE28A': 52,
    # Sports & Outdoors > Sportswear -> Mode & Vêtements
    '66C86053-159B-436E-B4A9-4A7CCB5CAC8A': 52,
    # Home Improvement > LED Lighting -> Maison & Jardin
    '392D3DB2-1E98-474E-9E45-9F2FE95A7608': 67,
    # Home Improvement > Indoor Lighting -> Maison & Jardin
    'BEFFF5CB-EF79-4984-9C55-62C23B95C0F7': 67,
    # Home Improvement > Outdoor Lighting -> Maison & Jardin
    '59AEBD05-0FDB-4392-BCF5-518C411A26E0': 67,
    # Home Improvement > Home Appliances -> Maison & Jardin
    '85EF081C-819E-448F-BD5C-C5D3F4CFAADA': 67,
}


def get_cj_l2_cj_id(cj_cat):
    """Remonter au niveau 2 et retourner son cj_category_id"""
    current = cj_cat
    while current.parent and current.level > 2:
        current = current.parent
    if current.level == 2:
        return current.cj_category_id
    return None


with app.app_context():
    print("\n" + "="*80)
    print("REMAPPING AFFINÉ NIVEAU 2")
    print("="*80 + "\n")
    
    products = Product.query.filter(Product.cj_pid.isnot(None)).all()
    
    fixed_l2 = 0
    fixed_orphan = 0
    details = []
    
    for p in products:
        if not p.cj_raw_data:
            continue
        try:
            raw = json.loads(p.cj_raw_data)
        except:
            continue
        
        cj_cat_id = str(raw.get('categoryId') or raw.get('category_id') or '')
        
        # --- 1. Traiter les produits avec catégorie CJ connue ---
        if cj_cat_id:
            cj_cat = Category.query.filter_by(cj_category_id=cj_cat_id).first()
            if cj_cat:
                # Vérifier si la sous-catégorie L2 a un override
                l2_cj_id = get_cj_l2_cj_id(cj_cat)
                if l2_cj_id and l2_cj_id in CJ_L2_OVERRIDES:
                    target = CJ_L2_OVERRIDES[l2_cj_id]
                    if p.category_id != target:
                        old_cat = Category.query.get(p.category_id)
                        new_cat = Category.query.get(target)
                        details.append(f"  [L2] {p.name[:50]} : {old_cat.name if old_cat else '?'} -> {new_cat.name if new_cat else '?'}")
                        p.category_id = target
                        fixed_l2 += 1
                continue
        
        # --- 2. Traiter les orphelins (catégorie CJ non trouvée) ---
        name_lower = p.name.lower()
        cj_cat_name = raw.get('categoryName', '').lower()
        target = None
        
        # Par categoryName CJ
        if "women's clothing" in cj_cat_name or "men's clothing" in cj_cat_name:
            target = 52
        elif "health" in cj_cat_name or "beauty" in cj_cat_name:
            target = 87
        elif "home" in cj_cat_name and "improvement" not in cj_cat_name:
            target = 67
        elif "packing" in cj_cat_name or "packaging" in cj_cat_name:
            target = 67
        
        # Par nom de produit
        if not target:
            if any(kw in name_lower for kw in ['dress', 'lingerie', 'bra', 'underwear', 'panties',
                'bodysuit', 'swimsuit', 'bikini', 'legging', 'corset', 'nightgown',
                'sleepwear', 'sexy', 'maid', 'belly band', 'sheer', 'lace set',
                'stocking', 'romper', 'jumpsuit', 'blouse', 'skirt', 'costume',
                'shapewear', 'bustier', 'thong', 'camisole', 'negligee', 'outfit',
                'clothing', 'shirt', 'pants', 'jacket', 'coat', 'sweater', 'hoodie',
                'hat', 'scarf', 'glove', 'sock', 'shoe', 'boot', 'sandal', 'slipper',
                'wig', 'hair extension']):
                target = 52
            elif any(kw in name_lower for kw in ['massage', 'massager', 'fascial gun',
                'moisturizing', 'hydrating', 'skin', 'beauty', 'cosmetic', 'health']):
                target = 87
            elif any(kw in name_lower for kw in ['packaging', 'express bag', 'hang tag',
                'logistics', 'biodegradable', 'delivery bag', 'sticker', 'card',
                'pillow', 'cushion', 'blanket', 'storage', 'box']):
                target = 67
            elif any(kw in name_lower for kw in ['toy', 'puzzle', 'plush', 'doll', 'fidget']):
                target = 126
            elif any(kw in name_lower for kw in ['phone', 'cable', 'charger', 'bluetooth']):
                target = 38
            elif any(kw in name_lower for kw in ['pet', 'dog', 'cat ']):
                target = 178
        
        if target and p.category_id != target:
            old_cat = Category.query.get(p.category_id)
            new_cat = Category.query.get(target)
            details.append(f"  [ORP] {p.name[:50]} : {old_cat.name if old_cat else '?'} -> {new_cat.name if new_cat else '?'}")
            p.category_id = target
            fixed_orphan += 1
    
    db.session.commit()
    
    print(f"Corrigés par override L2: {fixed_l2}")
    print(f"Corrigés orphelins:       {fixed_orphan}")
    print(f"Total corrigés:           {fixed_l2 + fixed_orphan}")
    print()
    
    for d in details:
        print(d)
    
    # Distribution finale
    print(f"\n{'='*80}")
    print("DISTRIBUTION FINALE")
    print(f"{'='*80}\n")
    
    from sqlalchemy import func
    dist = Product.query.filter(Product.cj_pid.isnot(None)).with_entities(
        Product.category_id, func.count(Product.id)
    ).group_by(Product.category_id).all()
    
    for cat_id, count in sorted(dist, key=lambda x: x[1], reverse=True):
        cat = Category.query.get(cat_id) if cat_id else None
        name = cat.name if cat else 'AUCUNE'
        print(f"  {name:<35} : {count:>6}")
    
    total = sum(c for _, c in dist)
    print(f"\n  {'TOTAL':<35} : {total:>6}")
    
    # Vérifier les orphelins restants
    print(f"\n{'='*80}")
    print("ORPHELINS RESTANTS")
    print(f"{'='*80}\n")
    
    remaining = 0
    for p in products:
        if not p.cj_raw_data:
            continue
        try:
            raw = json.loads(p.cj_raw_data)
        except:
            continue
        cj_cat_id = str(raw.get('categoryId') or raw.get('category_id') or '')
        if not cj_cat_id:
            cat = Category.query.get(p.category_id) if p.category_id else None
            print(f"  ID:{p.id:5} | {p.name[:55]:<55} | {cat.name if cat else '?'}")
            remaining += 1
            continue
        cj_cat = Category.query.filter_by(cj_category_id=cj_cat_id).first()
        if not cj_cat:
            cat = Category.query.get(p.category_id) if p.category_id else None
            print(f"  ID:{p.id:5} | {p.name[:55]:<55} | {cat.name if cat else '?'}")
            remaining += 1
    
    print(f"\nTotal orphelins restants: {remaining}")
