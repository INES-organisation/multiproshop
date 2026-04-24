"""
1. Trouver et traduire les catégories MPS L2/L3 encore en anglais
2. Reclasser les 99 orphelins dans les catégories MPS L3 les plus appropriées
"""
import sys, os, json, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.product import Product
from models.category import Category
from extensions import db

app = create_app()

# Traductions manquantes
MISSING_TRANSLATIONS = {
    # Computer & Office
    'Office & School Supplies': 'Fournitures de Bureau',
    'Tablet & Laptop Accessories': 'Accessoires Tablettes & PC',
    'Security & Protection': 'Sécurité & Protection',
    'Surveillance Products': 'Produits de Surveillance',
    'Tablet Cases': 'Coques Tablettes',
    'Beauty Tools': 'Outils Beauté',
    'LED Lighting': 'Éclairage LED',
    'Indoor Lighting': 'Éclairage Intérieur',
    'Outdoor Lighting': 'Éclairage Extérieur',
    'Home Appliances': 'Électroménager',
    # Manquantes identifiées
    'Laptop Stands': 'Supports PC Portable',
    'Laptop LCD Screen': 'Écrans PC Portable',
    'Laptop Batteries': 'Batteries PC Portable',
    'Laptop Bags & Cases': 'Sacoches & Housses PC',
    'Modem-Router Combos': 'Modems-Routeurs',
    'Networking Tools': 'Outils Réseau',
    'PDAs': 'PDA',
    'Printers': 'Imprimantes',
    'Tablets': 'Tablettes',
    'Tablet Accessories': 'Accessoires Tablettes',
    'Tablet LCDs & Panels': 'Écrans Tablettes',
    'Tablet Parts': 'Pièces Tablettes',
}

with app.app_context():
    # 1. Trouver les catégories non traduites (noms en anglais)
    print("=== TRADUCTION DES CATÉGORIES MANQUANTES ===\n")
    
    new_cats = Category.query.filter(
        Category.level >= 2,
        Category.cj_category_id.is_(None)  # Nouvelles catégories MPS (pas CJ)
    ).all()
    
    translated = 0
    still_english = []
    
    for cat in new_cats:
        if cat.name in MISSING_TRANSLATIONS:
            old_name = cat.name
            cat.name = MISSING_TRANSLATIONS[cat.name]
            cat.name_fr = cat.name
            print(f"  {old_name} -> {cat.name}")
            translated += 1
        else:
            # Vérifier si le nom contient des caractères anglais typiques
            has_french = any(c in cat.name for c in 'àâäéèêëïîôùûüÿçœæÀÂÄÉÈÊËÏÎÔÙÛÜŸÇŒÆ')
            has_common_en = any(w in cat.name.lower() for w in ['the ', 'and ', ' of ', ' for ', ' with '])
            if not has_french and has_common_en:
                still_english.append(f"  ID:{cat.id} | {cat.full_path}")
    
    db.session.commit()
    print(f"\nTraduit: {translated}")
    
    if still_english:
        print(f"\nEncore en anglais ({len(still_english)}):")
        for s in still_english:
            print(s)
    
    # 2. Lister toutes les catégories L2/L3 encore en anglais
    print(f"\n=== CATÉGORIES MPS L2/L3 ENCORE EN ANGLAIS ===\n")
    
    en_cats = []
    for cat in new_cats:
        # Heuristique : si le nom ne contient aucun caractère accentué français
        # et n'est pas un mot international (LED, USB, etc.)
        name = cat.name
        international = ['LED', 'USB', 'LCD', 'GPS', 'DVR', 'PDA', 'SIM', 'WiFi',
                         'Bluetooth', 'Quad Core', 'Octa Core', 'Leggings', 'Blazers',
                         'Boxers', 'Bikinis', 'Fedoras', 'Parkas', 'Golf', 'T-Shirts']
        if name in international:
            continue
        
        has_french = any(c in name for c in 'àâäéèêëïîôùûüÿçœæÀÂÄÉÈÊËÏÎÔÙÛÜŸÇŒÆ')
        # Mots anglais courants
        en_words = ['the ', ' and ', ' of ', ' for ', ' with ', ' in ', ' on ',
                    'tools', 'bags', 'shoes', 'cases', 'covers', 'parts',
                    'accessories', 'supplies', 'products', 'equipment']
        has_en = any(w in name.lower() for w in en_words)
        
        if has_en and not has_french:
            en_cats.append(cat)
    
    for cat in sorted(en_cats, key=lambda x: x.full_path):
        print(f"  ID:{cat.id:<5} L{cat.level} | {cat.full_path}")
    
    print(f"\nTotal encore en anglais: {len(en_cats)}")
    
    # 3. Orphelins
    print(f"\n=== ORPHELINS (99 produits) ===\n")
    
    products = Product.query.filter(Product.cj_pid.isnot(None)).all()
    orphans = []
    for p in products:
        if not p.cj_raw_data:
            orphans.append(p)
            continue
        try:
            raw = json.loads(p.cj_raw_data)
            cid = str(raw.get('categoryId') or raw.get('category_id') or '')
            if not cid:
                orphans.append(p)
        except:
            orphans.append(p)
    
    print(f"Orphelins trouvés: {len(orphans)}")
    
    # Vérifier dans quelle catégorie MPS ils sont actuellement
    for p in orphans[:20]:
        cat = db.session.get(Category, p.category_id) if p.category_id else None
        print(f"  ID:{p.id:<6} | {p.name[:50]:<50} | {cat.full_path if cat else '?'}")
