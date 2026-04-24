"""
Construire le mapping CJ catégorie niveau 1 -> MPS catégorie
et lister toutes les catégories CJ niveau 1 avec le nombre de produits
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
    print("CATEGORIES CJ NIVEAU 1 (PRINCIPALES)")
    print("="*80 + "\n")
    
    # Récupérer toutes les catégories CJ niveau 1
    cj_level1 = Category.query.filter(
        Category.cj_category_id.isnot(None),
        Category.level == 1
    ).order_by(Category.name).all()
    
    print(f"{'Catégorie CJ Niveau 1':<40} | {'CJ ID':<40} | {'ID BDD':>6}")
    print("-" * 95)
    for cat in cj_level1:
        print(f"{cat.name:<40} | {cat.cj_category_id:<40} | {cat.id:>6}")
    
    # Récupérer toutes les catégories MPS niveau 1
    print("\n" + "="*80)
    print("CATEGORIES MPS NIVEAU 1 (PRINCIPALES)")
    print("="*80 + "\n")
    
    mps_level1 = Category.query.filter(
        Category.cj_category_id == None,
        Category.level == 1,
        Category.visible == True
    ).order_by(Category.name).all()
    
    print(f"{'Catégorie MPS':<40} | {'ID BDD':>6}")
    print("-" * 50)
    for cat in mps_level1:
        print(f"{cat.name:<40} | {cat.id:>6}")
    
    # Analyser la distribution des produits par catégorie CJ niveau 1
    print("\n" + "="*80)
    print("DISTRIBUTION PRODUITS PAR CATEGORIE CJ NIVEAU 1 (depuis raw_data)")
    print("="*80 + "\n")
    
    products = Product.query.filter(Product.cj_pid.isnot(None)).all()
    
    # Pour chaque produit, trouver sa catégorie CJ niveau 1
    cj_l1_distribution = {}
    no_raw = 0
    no_cat = 0
    
    for p in products:
        if not p.cj_raw_data:
            no_raw += 1
            continue
        
        try:
            raw = json.loads(p.cj_raw_data)
            cj_cat_id = str(raw.get('category_id') or raw.get('categoryId') or '')
            
            if not cj_cat_id:
                no_cat += 1
                continue
            
            # Trouver la catégorie CJ
            cj_cat = Category.query.filter_by(cj_category_id=cj_cat_id).first()
            
            if cj_cat:
                # Remonter au niveau 1
                current = cj_cat
                while current.parent and current.level > 1:
                    current = current.parent
                
                l1_name = current.name
                if l1_name not in cj_l1_distribution:
                    cj_l1_distribution[l1_name] = 0
                cj_l1_distribution[l1_name] += 1
            else:
                if 'NON TROUVÉE' not in cj_l1_distribution:
                    cj_l1_distribution['NON TROUVÉE'] = 0
                cj_l1_distribution['NON TROUVÉE'] += 1
                
        except (json.JSONDecodeError, TypeError):
            no_raw += 1
    
    print(f"Produits sans raw_data: {no_raw}")
    print(f"Produits sans category_id: {no_cat}")
    print()
    
    sorted_dist = sorted(cj_l1_distribution.items(), key=lambda x: x[1], reverse=True)
    
    print(f"{'Catégorie CJ Niveau 1':<40} | {'Produits':>8}")
    print("-" * 55)
    for name, count in sorted_dist:
        print(f"{name:<40} | {count:>8}")
    
    total = sum(c for _, c in sorted_dist)
    print(f"{'TOTAL':<40} | {total:>8}")
