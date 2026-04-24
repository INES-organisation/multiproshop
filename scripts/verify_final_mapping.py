"""
Vérification finale du mapping CJ -> MPS
Vérifie que chaque produit est dans la bonne catégorie MPS
en comparant avec sa catégorie CJ originale.
"""
import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.product import Product
from models.category import Category

# Mapping attendu CJ L1 -> MPS ID
EXPECTED = {
    'Phones & Accessories': 38,
    'Computer & Office': 22,
    'Home, Garden & Furniture': 67,
    "Women's Clothing": 52,
    'Jewelry & Watches': 52,
    "Men's Clothing": 52,
    'Bags & Shoes': 52,
    'Health, Beauty & Hair': 87,
    'Automobiles & Motorcycles': 139,
    'Sports & Outdoors': 100,
    'Home Improvement': 152,
    'Pet Supplies': 178,
    'Consumer Electronics': 1,
    'Toys, Kids & Babies': None,  # Spécial, géré par sous-catégorie
}

TOYS_L2 = {
    'Toys & Hobbies': 126,
    'Baby Clothing': 113,
    'Baby & Mother': 113,
    'Boys Clothing': 52,
    'Girls Clothing': 52,
    'Shoes & Bags': 52,
}

app = create_app()

with app.app_context():
    print("\n" + "="*80)
    print("VERIFICATION FINALE DU MAPPING")
    print("="*80 + "\n")
    
    products = Product.query.filter(Product.cj_pid.isnot(None)).all()
    
    correct = 0
    incorrect = 0
    skipped = 0
    incorrect_examples = []
    
    for p in products:
        if not p.cj_raw_data:
            skipped += 1
            continue
        
        try:
            raw = json.loads(p.cj_raw_data)
        except:
            skipped += 1
            continue
        
        cj_cat_id = str(raw.get('categoryId') or raw.get('category_id') or '')
        if not cj_cat_id:
            skipped += 1
            continue
        
        cj_cat = Category.query.filter_by(cj_category_id=cj_cat_id).first()
        if not cj_cat:
            skipped += 1
            continue
        
        # Remonter au niveau 1
        current = cj_cat
        while current.parent and current.level > 1:
            current = current.parent
        l1_name = current.name
        
        # Déterminer le MPS attendu
        expected_mps = EXPECTED.get(l1_name)
        
        if l1_name == 'Toys, Kids & Babies':
            # Remonter au niveau 2
            current2 = cj_cat
            while current2.parent and current2.level > 2:
                current2 = current2.parent
            l2_name = current2.name if current2.level == 2 else None
            expected_mps = TOYS_L2.get(l2_name, 126)
        
        if expected_mps is None:
            skipped += 1
            continue
        
        if p.category_id == expected_mps:
            correct += 1
        else:
            incorrect += 1
            if len(incorrect_examples) < 20:
                actual_cat = Category.query.get(p.category_id) if p.category_id else None
                expected_cat = Category.query.get(expected_mps)
                incorrect_examples.append({
                    'name': p.name[:60],
                    'cj_l1': l1_name,
                    'actual': actual_cat.name if actual_cat else 'AUCUNE',
                    'expected': expected_cat.name if expected_cat else '?',
                })
    
    total = correct + incorrect + skipped
    print(f"Total produits CJ: {total}")
    print(f"  Corrects:   {correct} ({correct*100//(correct+incorrect) if correct+incorrect else 0}%)")
    print(f"  Incorrects: {incorrect}")
    print(f"  Ignorés:    {skipped}")
    
    if incorrect_examples:
        print(f"\n--- Exemples de produits mal mappés ({len(incorrect_examples)} premiers) ---\n")
        for ex in incorrect_examples:
            print(f"  {ex['name']}")
            print(f"    CJ L1: {ex['cj_l1']} | Actuel: {ex['actual']} | Attendu: {ex['expected']}")
            print()
    else:
        print("\n✅ AUCUNE INCOHÉRENCE DÉTECTÉE ! Mapping parfait.")
    
    # Vérifier le Dual Monitor spécifiquement
    print("\n--- Vérification Dual Monitor ---")
    dual = Product.query.filter(Product.name.ilike('%dual monitor%')).first()
    if dual:
        cat = Category.query.get(dual.category_id)
        print(f"  Produit: {dual.name[:60]}")
        print(f"  Catégorie: {cat.name if cat else 'AUCUNE'} (ID: {dual.category_id})")
    else:
        print("  Produit Dual Monitor non trouvé")
    
    # Distribution finale
    print("\n--- Distribution par catégorie MPS ---\n")
    from sqlalchemy import func
    dist = Product.query.filter(Product.cj_pid.isnot(None)).with_entities(
        Product.category_id, func.count(Product.id)
    ).group_by(Product.category_id).all()
    
    for cat_id, count in sorted(dist, key=lambda x: x[1], reverse=True):
        cat = Category.query.get(cat_id) if cat_id else None
        name = cat.name if cat else 'AUCUNE'
        print(f"  {name:<35} : {count:>6}")
