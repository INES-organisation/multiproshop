"""
Script pour analyser spécifiquement la catégorie Mode & Vêtements
et identifier tous les produits qui n'y ont pas leur place
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.product import Product
from models.category import Category

app = create_app()

with app.app_context():
    # Catégorie Mode & Vêtements
    mode_cat = Category.query.get(52)
    
    print("\n" + "="*100)
    print(f"ANALYSE DÉTAILLÉE: {mode_cat.name} (ID: 52)")
    print("="*100 + "\n")
    
    products = Product.query.filter_by(category_id=52).all()
    total = len(products)
    
    print(f"Total produits: {total}\n")
    
    # Identifier les produits suspects (auto, électronique, etc.)
    suspects = {
        'auto': [],
        'electronique': [],
        'maison': [],
        'autre': []
    }
    
    auto_keywords = ['sensor', 'brake', 'abs', 'wheel', 'car', 'vehicle', 'automotive', 'mercedes', 'bmw']
    elec_keywords = ['charger', 'cable', 'bluetooth', 'wireless', 'phone holder']
    home_keywords = ['lamp', 'light', 'furniture', 'decoration']
    
    for p in products:
        name_lower = p.name.lower()
        
        # Vérifier si c'est un produit auto
        if any(kw in name_lower for kw in auto_keywords):
            suspects['auto'].append(p)
        # Vérifier si c'est un produit électronique
        elif any(kw in name_lower for kw in elec_keywords):
            suspects['electronique'].append(p)
        # Vérifier si c'est un produit maison
        elif any(kw in name_lower for kw in home_keywords):
            suspects['maison'].append(p)
    
    # Afficher les suspects
    if suspects['auto']:
        print(f"\n🚗 PRODUITS AUTO DÉTECTÉS ({len(suspects['auto'])} produits):")
        print("-" * 100)
        for p in suspects['auto'][:20]:
            print(f"  - {p.name[:90]}")
    
    if suspects['electronique']:
        print(f"\n📱 PRODUITS ÉLECTRONIQUE DÉTECTÉS ({len(suspects['electronique'])} produits):")
        print("-" * 100)
        for p in suspects['electronique'][:20]:
            print(f"  - {p.name[:90]}")
    
    if suspects['maison']:
        print(f"\n🏠 PRODUITS MAISON DÉTECTÉS ({len(suspects['maison'])} produits):")
        print("-" * 100)
        for p in suspects['maison'][:20]:
            print(f"  - {p.name[:90]}")
    
    total_suspects = len(suspects['auto']) + len(suspects['electronique']) + len(suspects['maison'])
    print(f"\n\n⚠️ TOTAL SUSPECTS: {total_suspects} produits sur {total} ({total_suspects*100/total:.1f}%)")
    print("="*100 + "\n")
