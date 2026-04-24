"""
Corriger les derniers produits orphelins restants + vérification approfondie.
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

with app.app_context():
    products = Product.query.filter(Product.cj_pid.isnot(None)).all()
    
    # 1. Trouver les produits encore orphelins
    orphans = []
    for p in products:
        if not p.cj_raw_data:
            continue
        try:
            raw = json.loads(p.cj_raw_data)
        except:
            continue
        
        cj_cat_id = str(raw.get('categoryId') or raw.get('category_id') or '')
        if not cj_cat_id:
            orphans.append(p)
            continue
        
        cj_cat = Category.query.filter_by(cj_category_id=cj_cat_id).first()
        if not cj_cat:
            orphans.append(p)
    
    print(f"\nOrphelins restants: {len(orphans)}\n")
    
    for p in orphans:
        raw = json.loads(p.cj_raw_data) if p.cj_raw_data else {}
        cj_name = raw.get('categoryName', '')
        cat = Category.query.get(p.category_id) if p.category_id else None
        print(f"  ID:{p.id:5} | {p.name[:55]:<55} | Actuel: {cat.name if cat else '?':<25} | CJ: {cj_name}")
    
    # 2. Corriger manuellement les orphelins restants
    fixes = {}
    for p in orphans:
        name_lower = p.name.lower()
        raw = json.loads(p.cj_raw_data) if p.cj_raw_data else {}
        cj_name = raw.get('categoryName', '').lower()
        
        # Sleepwear, lingerie, sexy, maid, bikini -> Mode (52)
        if any(kw in name_lower for kw in ['sleepwear', 'sexy', 'maid', 'lingerie', 'bikini', 
                                             'belly band', 'embroidery', 'sheer', 'lace set',
                                             'floral', 'outfit']):
            fixes[p.id] = 52
        # Fascial gun, massage -> Santé (87)
        elif any(kw in name_lower for kw in ['fascial gun', 'massage gun']):
            fixes[p.id] = 87
        # Moisturizing, hydrating, skin -> Santé (87)
        elif any(kw in name_lower for kw in ['moisturizing', 'hydrating', 'skin']):
            fixes[p.id] = 87
        # Packaging, express bag, hang tag -> Maison (67)
        elif any(kw in name_lower for kw in ['packaging', 'express bag', 'hang tag', 'logistics',
                                              'biodegradable', 'delivery bag']):
            fixes[p.id] = 67
        # Customized cards, thank you card -> déjà corrigé
        elif 'card' in name_lower and p.category_id == 139:
            # "Customized Cards" et "Thank You Card" -> Maison & Jardin plutôt qu'Auto
            fixes[p.id] = 67
    
    # Appliquer les corrections
    fixed_count = 0
    for pid, target_id in fixes.items():
        p = Product.query.get(pid)
        if p and p.category_id != target_id:
            old_cat = Category.query.get(p.category_id)
            new_cat = Category.query.get(target_id)
            print(f"\n  FIX: {p.name[:50]} : {old_cat.name if old_cat else '?'} -> {new_cat.name if new_cat else '?'}")
            p.category_id = target_id
            fixed_count += 1
    
    db.session.commit()
    print(f"\n\nCorrigés: {fixed_count}")
    
    # 3. Vérification approfondie : échantillon aléatoire par catégorie MPS
    print(f"\n{'='*80}")
    print("VERIFICATION APPROFONDIE - Échantillon par catégorie MPS")
    print(f"{'='*80}\n")
    
    mps_cats = [
        (1, 'Électronique & High-Tech'),
        (22, 'Informatique'),
        (38, 'Téléphonie & Tablettes'),
        (52, 'Mode & Vêtements'),
        (67, 'Maison & Jardin'),
        (87, 'Santé & Beauté'),
        (100, 'Sports & Loisirs'),
        (113, 'Bébés & Puériculture'),
        (126, 'Jeux & Jouets'),
        (139, 'Auto & Moto'),
        (152, 'Bricolage & Outillage'),
        (178, 'Animalerie'),
    ]
    
    for mps_id, mps_name in mps_cats:
        prods = Product.query.filter_by(category_id=mps_id).filter(
            Product.cj_pid.isnot(None)
        ).limit(15).all()
        
        print(f"\n--- {mps_name} (ID:{mps_id}) - {len(prods)} premiers ---")
        for p in prods:
            print(f"  {p.name[:70]}")
