"""
Script pour vérifier les incohérences de catégories sur /products/
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.product import Product
from models.category import Category

app = create_app()

with app.app_context():
    print("\n" + "="*80)
    print("VERIFICATION CATEGORIES SUR /products/")
    print("="*80 + "\n")
    
    # Vérifier 30 premiers produits affichés sur /products/
    prods = Product.query.limit(30).all()
    
    print(f"{'Produit':<50} | {'Catégorie':<30} | CJ")
    print("-" * 90)
    
    incoherences = []
    
    for p in prods:
        cat_name = p.category.name if p.category else "AUCUNE"
        is_cj = "Oui" if p.cj_pid else "Non"
        
        print(f"{p.name[:50]:<50} | {cat_name[:30]:<30} | {is_cj}")
        
        # Détecter les incohérences
        if p.category:
            # Produits informatique dans Mode
            if 'monitor' in p.name.lower() or 'keyboard' in p.name.lower() or 'mouse' in p.name.lower():
                if 'mode' in p.category.name.lower() or 'vêtement' in p.category.name.lower():
                    incoherences.append({
                        'produit': p.name,
                        'categorie_actuelle': p.category.name,
                        'categorie_attendue': 'Informatique ou Électronique'
                    })
    
    if incoherences:
        print("\n" + "="*80)
        print("INCOHÉRENCES DÉTECTÉES")
        print("="*80 + "\n")
        
        for inc in incoherences:
            print(f"❌ {inc['produit'][:60]}")
            print(f"   Catégorie actuelle: {inc['categorie_actuelle']}")
            print(f"   Catégorie attendue: {inc['categorie_attendue']}")
            print()
    else:
        print("\n✅ Aucune incohérence détectée dans les 30 premiers produits")
