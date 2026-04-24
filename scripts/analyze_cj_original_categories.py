"""
Analyser les catégories CJ originales des produits pour créer un mapping CJ -> MPS
"""
import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.product import Product
from models.category import Category

app = create_app()

with app.app_context():
    print("\n" + "="*80)
    print("ANALYSE DES CATEGORIES CJ ORIGINALES")
    print("="*80 + "\n")
    
    # 1. Récupérer tous les produits CJ avec raw_data
    products = Product.query.filter(Product.cj_pid.isnot(None)).all()
    print(f"Total produits CJ: {len(products)}")
    
    # 2. Extraire les category_id CJ originaux depuis raw_data
    cj_cat_ids = {}  # cj_category_id -> count
    products_without_raw = 0
    products_without_cat = 0
    
    for p in products:
        if p.cj_raw_data:
            try:
                raw = json.loads(p.cj_raw_data)
                cj_cat_id = raw.get('category_id') or raw.get('categoryId')
                if cj_cat_id:
                    cj_cat_id = str(cj_cat_id)
                    if cj_cat_id not in cj_cat_ids:
                        cj_cat_ids[cj_cat_id] = {'count': 0, 'examples': []}
                    cj_cat_ids[cj_cat_id]['count'] += 1
                    if len(cj_cat_ids[cj_cat_id]['examples']) < 3:
                        cj_cat_ids[cj_cat_id]['examples'].append(p.name[:60])
                else:
                    products_without_cat += 1
            except (json.JSONDecodeError, TypeError):
                products_without_raw += 1
        else:
            products_without_raw += 1
    
    print(f"Produits sans raw_data: {products_without_raw}")
    print(f"Produits sans category_id dans raw_data: {products_without_cat}")
    print(f"Catégories CJ uniques trouvées: {len(cj_cat_ids)}")
    
    # 3. Afficher les catégories CJ et les mapper vers les catégories MPS existantes
    print("\n" + "="*80)
    print("CATEGORIES CJ ORIGINALES -> CATEGORIES CJ EN BDD")
    print("="*80 + "\n")
    
    sorted_cats = sorted(cj_cat_ids.items(), key=lambda x: x[1]['count'], reverse=True)
    
    for cj_id, info in sorted_cats:
        # Chercher la catégorie CJ en BDD
        cj_cat = Category.query.filter_by(cj_category_id=cj_id).first()
        cat_name = cj_cat.name if cj_cat else "NON TROUVÉE"
        cat_level = cj_cat.level if cj_cat else "?"
        parent_name = ""
        if cj_cat and cj_cat.parent:
            parent_name = cj_cat.parent.name
            if cj_cat.parent.parent:
                parent_name = cj_cat.parent.parent.name + " > " + parent_name
        
        print(f"CJ ID: {cj_id:15} | Produits: {info['count']:5} | Niveau: {cat_level} | {cat_name}")
        if parent_name:
            print(f"{'':15}   Chemin: {parent_name}")
        for ex in info['examples']:
            print(f"{'':15}   Ex: {ex}")
        print()
    
    # 4. Vérifier le produit Dual Monitor spécifiquement
    print("\n" + "="*80)
    print("VERIFICATION PRODUIT DUAL MONITOR")
    print("="*80 + "\n")
    
    dual = Product.query.filter(Product.name.ilike('%dual monitor%')).first()
    if dual:
        print(f"Produit: {dual.name}")
        print(f"Category ID actuel: {dual.category_id}")
        cat = Category.query.get(dual.category_id)
        print(f"Catégorie actuelle: {cat.name if cat else 'AUCUNE'}")
        
        if dual.cj_raw_data:
            raw = json.loads(dual.cj_raw_data)
            cj_cat_id = raw.get('category_id') or raw.get('categoryId')
            print(f"CJ Category ID original: {cj_cat_id}")
            
            if cj_cat_id:
                cj_cat = Category.query.filter_by(cj_category_id=str(cj_cat_id)).first()
                if cj_cat:
                    print(f"Catégorie CJ: {cj_cat.name} (chemin: {cj_cat.full_path})")
                else:
                    print(f"Catégorie CJ non trouvée en BDD")
        else:
            print("Pas de raw_data")
