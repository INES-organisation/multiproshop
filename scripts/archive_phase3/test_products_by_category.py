"""
Tester la récupération des produits par catégorie avec sous-catégories
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from app import create_app
from models.product import Product
from models.category import Category

app = create_app()

with app.app_context():
    print("\n" + "="*70)
    print("TEST RÉCUPÉRATION PRODUITS PAR CATÉGORIE")
    print("="*70 + "\n")
    
    # Test 1: Catégorie niveau 3 avec produits
    print("1. TEST CATÉGORIE NIVEAU 3 (Computer Tablet Accessories)")
    print("-" * 70)
    
    cat3 = Category.query.filter(
        Category.name == "Computer Tablet Accessories",
        Category.cj_category_id.isnot(None)
    ).first()
    
    if cat3:
        print(f"Catégorie: {cat3.name}")
        print(f"  CJ ID: {cat3.cj_category_id}")
        print(f"  Niveau: {cat3.level}")
        
        # Simuler la logique de la route
        category_ids = [cat3.id]
        
        products = Product.query.filter(
            Product.category_id.in_(category_ids),
            Product.cj_pid.isnot(None)
        ).all()
        
        print(f"\nProduits trouvés: {len(products)}")
        if products:
            print(f"Exemples (5 premiers):")
            for p in products[:5]:
                print(f"  - {p.name[:50]}")
    
    # Test 2: Catégorie niveau 1 avec sous-catégories
    print("\n2. TEST CATÉGORIE NIVEAU 1 (Automobiles & Motorcycles)")
    print("-" * 70)
    
    cat1 = Category.query.filter(
        Category.name == "Automobiles & Motorcycles",
        Category.cj_category_id.isnot(None)
    ).first()
    
    if cat1:
        print(f"Catégorie: {cat1.name}")
        print(f"  CJ ID: {cat1.cj_category_id}")
        print(f"  Niveau: {cat1.level}")
        
        # Simuler la logique de la route
        category_ids = [cat1.id]
        
        # Ajouter niveau 2
        level2_cats = Category.query.filter_by(parent_id=cat1.id).all()
        print(f"\nSous-catégories niveau 2: {len(level2_cats)}")
        
        for cat2 in level2_cats:
            category_ids.append(cat2.id)
            # Ajouter niveau 3
            level3_cats = Category.query.filter_by(parent_id=cat2.id).all()
            category_ids.extend([cat3.id for cat3 in level3_cats])
            
            if level3_cats:
                print(f"  - {cat2.name}: {len(level3_cats)} sous-catégories niveau 3")
        
        print(f"\nTotal catégories concernées: {len(category_ids)}")
        
        products = Product.query.filter(
            Product.category_id.in_(category_ids),
            Product.cj_pid.isnot(None)
        ).all()
        
        print(f"Produits trouvés: {len(products)}")
        
        if products:
            print(f"\nExemples (5 premiers):")
            for p in products[:5]:
                print(f"  - {p.name[:50]}")
                cat = Category.query.get(p.category_id)
                print(f"    Catégorie: {cat.name if cat else 'N/A'}")
    else:
        print("Catégorie 'Automobiles & Motorcycles' non trouvée")
    
    # Test 3: Statistiques globales
    print("\n3. STATISTIQUES GLOBALES")
    print("-" * 70)
    
    total_cj = Product.query.filter(Product.cj_pid.isnot(None)).count()
    published = Product.query.filter(
        Product.cj_pid.isnot(None),
        Product.published == True
    ).count()
    in_stock = Product.query.filter(
        Product.cj_pid.isnot(None),
        Product.stock > 0
    ).count()
    
    print(f"Total produits CJ: {total_cj}")
    print(f"Produits publiés: {published}")
    print(f"Produits en stock: {in_stock}")
    
    print("\n" + "="*70 + "\n")
