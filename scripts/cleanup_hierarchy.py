"""
Nettoyage de la hiérarchie MPS :
1. Traduire les catégories L3 encore en anglais
2. Identifier les catégories L2 vides pré-existantes (avant la fusion CJ)
3. Identifier les doublons
4. Reclasser les produits directement dans L1
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.product import Product
from models.category import Category
from extensions import db
from sqlalchemy import func

app = create_app()

# Traductions L3 manquantes
L3_TRANSLATIONS = {
    'Eyebrow Pencil': 'Crayons Sourcils',
    'Eyeshadow': 'Fards à Paupières',
    'False Eyelashes': 'Faux Cils',
    'Lipstick': 'Rouges à Lèvres',
    'Makeup Brushes': 'Pinceaux Maquillage',
    'Makeup Set': 'Coffrets Maquillage',
    'Nail Art Kits': 'Kits Nail Art',
    'Nail Decorations': 'Décorations Ongles',
    'Nail Glitters': 'Paillettes Ongles',
    'Body Care': 'Soins du Corps',
    'Face Masks': 'Masques Visage',
    'Facial Care': 'Soins du Visage',
    'Razor': 'Rasoirs',
    'Human Hair Wigs': 'Perruques Naturelles',
    'Synthetic Wigs': 'Perruques Synthétiques',
    'Hair Weaving': 'Tissage Cheveux',
    'Hair Weaves': 'Tissages',
    'Food & Health': 'Alimentation & Santé',
    'Curling Iron': 'Fer à Boucler',
    'Straightening Irons': 'Lisseurs',
    'Wigs & Extensions': 'Perruques & Extensions',
    # Auto
    'Exterior Accessories': 'Accessoires Extérieurs Auto',
    # Informatique
    'Office Supplies': 'Fournitures de Bureau',
    # Maison
    'Home Textiles': 'Textile Maison',
    'Seasonal products': 'Produits Saisonniers',
    # Divers
    'Rétroviseurs': 'Miroirs de Maquillage',  # Erreur de traduction CJ "Mirrors" dans Beauty
}

with app.app_context():
    print("="*80)
    print("NETTOYAGE DE LA HIÉRARCHIE MPS")
    print("="*80)
    
    # 1. Traduire les L3 encore en anglais
    print("\n--- 1. Traduction des catégories restantes ---\n")
    
    all_cats = Category.query.filter(Category.level >= 2).all()
    translated = 0
    
    for cat in all_cats:
        if cat.name in L3_TRANSLATIONS:
            old = cat.name
            cat.name = L3_TRANSLATIONS[cat.name]
            cat.name_fr = cat.name
            print(f"  {old:<35} -> {cat.name}")
            translated += 1
    
    db.session.commit()
    print(f"  Traduit: {translated}")
    
    # 2. Identifier les catégories L2 vides (0 produits, 0 sous-catégories avec produits)
    print("\n--- 2. Catégories L2/L3 vides ---\n")
    
    empty_cats = []
    for cat in all_cats:
        # Compter les produits directs
        direct = Product.query.filter_by(category_id=cat.id).filter(
            Product.cj_pid.isnot(None)
        ).count()
        
        # Compter les produits dans les enfants
        children = Category.query.filter_by(parent_id=cat.id).all()
        child_total = 0
        for child in children:
            child_total += Product.query.filter_by(category_id=child.id).filter(
                Product.cj_pid.isnot(None)
            ).count()
            # Petits-enfants
            grandchildren = Category.query.filter_by(parent_id=child.id).all()
            for gc in grandchildren:
                child_total += Product.query.filter_by(category_id=gc.id).filter(
                    Product.cj_pid.isnot(None)
                ).count()
        
        if direct == 0 and child_total == 0:
            empty_cats.append(cat)
    
    # Séparer : pré-existantes (avec cj_category_id ou sans) vs nouvelles
    pre_existing = [c for c in empty_cats if c.cj_category_id is not None]
    new_empty = [c for c in empty_cats if c.cj_category_id is None]
    
    print(f"  Catégories CJ vides (pré-existantes): {len(pre_existing)}")
    print(f"  Catégories MPS vides (nouvelles): {len(new_empty)}")
    
    for c in new_empty:
        print(f"    ID:{c.id:<5} L{c.level} | {c.full_path}")
    
    # 3. Identifier les doublons (même nom sous le même parent)
    print("\n--- 3. Doublons ---\n")
    
    parent_name_map = {}
    for cat in all_cats:
        if cat.cj_category_id:
            continue  # Ignorer les catégories CJ
        key = (cat.parent_id, cat.name)
        if key in parent_name_map:
            parent_name_map[key].append(cat)
        else:
            parent_name_map[key] = [cat]
    
    duplicates = {k: v for k, v in parent_name_map.items() if len(v) > 1}
    
    for (pid, name), cats in duplicates.items():
        parent = db.session.get(Category, pid) if pid else None
        print(f"  Doublon: '{name}' sous '{parent.name if parent else 'ROOT'}'")
        for c in cats:
            count = Product.query.filter_by(category_id=c.id).filter(
                Product.cj_pid.isnot(None)
            ).count()
            children_count = Category.query.filter_by(parent_id=c.id).count()
            print(f"    ID:{c.id:<5} | {count} produits | {children_count} enfants | cj_id: {c.cj_category_id or 'None'}")
    
    # 4. Produits directement dans L1
    print("\n--- 4. Produits directement dans L1 ---\n")
    
    mps_l1 = Category.query.filter_by(level=1).filter(
        Category.cj_category_id.is_(None)
    ).all()
    
    for l1 in mps_l1:
        direct = Product.query.filter_by(category_id=l1.id).filter(
            Product.cj_pid.isnot(None)
        ).count()
        if direct > 0:
            print(f"  {l1.name}: {direct} produits directement dans L1")
            prods = Product.query.filter_by(category_id=l1.id).filter(
                Product.cj_pid.isnot(None)
            ).limit(5).all()
            for p in prods:
                print(f"    {p.name[:60]}")
