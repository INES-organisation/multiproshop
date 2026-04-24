"""Traduire les 21 catégories MPS encore en anglais"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.category import Category
from extensions import db

app = create_app()

TRANSLATIONS = {
    1797: 'Autres Accessoires Extérieurs',
    1801: 'Autres Accessoires Moto',
    1791: 'Pièces Extérieures',
    1792: 'Pièces Intérieures',
    1793: 'Autres Pièces Détachées',
    1802: 'Entretien & Maintenance',
    1803: 'Autres Produits d\'Entretien',
    1922: 'Pièces Électroménager',
    1857: 'Sécurité au Travail',
    1847: 'Accessoires Tablettes & PC',
    1849: 'Consommables Imprimante',
    1949: 'Fournitures Événements & Fêtes',
    1963: 'Housses de Coussin',
    1957: 'Produits Saisonniers',
    1959: 'Sacs & Boîtes de Rangement',
    1819: 'Pochettes de Soirée',
    1824: 'Sacs Bandoulière Femme',
    1807: 'Sacs Fille',
    1812: 'Chaussures de Ville',
    1893: 'Produits de Santé',
    1894: 'Cheveux & Accessoires',
    1895: 'Bandeaux & Barrettes',
}

with app.app_context():
    fixed = 0
    for cat_id, fr_name in TRANSLATIONS.items():
        cat = db.session.get(Category, cat_id)
        if cat:
            old = cat.name
            cat.name = fr_name
            cat.name_fr = fr_name
            print(f"  {old:<45} -> {fr_name}")
            fixed += 1
        else:
            print(f"  ID:{cat_id} non trouvé !")
    
    db.session.commit()
    print(f"\nTraduit: {fixed}")
    
    # Vérifier qu'il ne reste plus de catégories en anglais
    new_cats = Category.query.filter(
        Category.level >= 2,
        Category.cj_category_id.is_(None)
    ).all()
    
    en_words = ['tools', 'bags', 'shoes', 'cases', 'covers', 'parts',
                'accessories', 'supplies', 'products', 'equipment',
                'the ', ' and ', ' of ', ' for ', ' with ']
    international = ['LED', 'USB', 'LCD', 'GPS', 'DVR', 'PDA', 'SIM',
                     'Bluetooth', 'Quad Core', 'Octa Core', 'Leggings', 'Blazers',
                     'Boxers', 'Bikinis', 'Fedoras', 'Parkas', 'Golf']
    
    still_en = []
    for cat in new_cats:
        if cat.name in international:
            continue
        if any(w in cat.name.lower() for w in en_words):
            still_en.append(f"  ID:{cat.id:<5} | {cat.full_path}")
    
    if still_en:
        print(f"\nEncore en anglais ({len(still_en)}):")
        for s in still_en:
            print(s)
    else:
        print("\nToutes les catégories sont traduites en français !")
