"""
Tester l'affichage des produits pour tous les niveaux de catégories
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
    print("TEST AFFICHAGE PRODUITS - TOUS NIVEAUX")
    print("="*70 + "\n")
    
    # Test niveau 1
    print("1. TEST NIVEAU 1 - Home, Garden & Furniture")
    print("-" * 70)
    
    cat1 = Category.query.filter(
        Category.name == "Home, Garden & Furniture",
        Category.cj_category_id.isnot(None),
        Category.level == 1
    ).first()
    
    if cat1:
        print(f"Catégorie: {cat1.name}")
        print(f"  Product count: {cat1.product_count}")
        
        # Simuler la logique de la route
        category_ids = [cat1.id]
        
        # Ajouter niveau 2
        level2_cats = Category.query.filter_by(parent_id=cat1.id).all()
        for cat2 in level2_cats:
            category_ids.append(cat2.id)
            # Ajouter niveau 3
            level3_cats = Category.query.filter_by(parent_id=cat2.id).all()
            category_ids.extend([cat3.id for cat3 in level3_cats])
        
        products = Product.query.filter(
            Product.category_id.in_(category_ids),
            Product.cj_pid.isnot(None)
        ).count()
        
        print(f"  Catégories concernées: {len(category_ids)}")
        print(f"  Produits trouvés: {products}")
        print(f"  ✓ Cohérence: {products == cat1.product_count}")
    
    # Test niveau 2
    print("\n2. TEST NIVEAU 2 - Home Textiles")
    print("-" * 70)
    
    cat2 = Category.query.filter(
        Category.name == "Home Textiles",
        Category.cj_category_id.isnot(None),
        Category.level == 2
    ).first()
    
    if cat2:
        print(f"Catégorie: {cat2.name}")
        print(f"  Product count: {cat2.product_count}")
        
        # Simuler la logique de la route
        category_ids = [cat2.id]
        
        # Ajouter niveau 3
        level3_cats = Category.query.filter_by(parent_id=cat2.id).all()
        category_ids.extend([cat3.id for cat3 in level3_cats])
        
        products = Product.query.filter(
            Product.category_id.in_(category_ids),
            Product.cj_pid.isnot(None)
        ).count()
        
        print(f"  Catégories concernées: {len(category_ids)}")
        print(f"  Produits trouvés: {products}")
        print(f"  ✓ Cohérence: {products == cat2.product_count}")
    
    # Test niveau 3
    print("\n3. TEST NIVEAU 3 - Comforters")
    print("-" * 70)
    
    cat3 = Category.query.filter(
        Category.name == "Comforters",
        Category.cj_category_id.isnot(None),
        Category.level == 3
    ).first()
    
    if cat3:
        print(f"Catégorie: {cat3.name}")
        print(f"  Product count: {cat3.product_count}")
        
        # Simuler la logique de la route
        category_ids = [cat3.id]
        
        products = Product.query.filter(
            Product.category_id.in_(category_ids),
            Product.cj_pid.isnot(None)
        ).count()
        
        print(f"  Catégories concernées: {len(category_ids)}")
        print(f"  Produits trouvés: {products}")
        print(f"  ✓ Cohérence: {products == cat3.product_count}")
        
        # Afficher quelques exemples
        examples = Product.query.filter(
            Product.category_id.in_(category_ids),
            Product.cj_pid.isnot(None)
        ).limit(3).all()
        
        print(f"\n  Exemples de produits:")
        for p in examples:
            print(f"    - {p.name[:60]}")
    
    print("\n" + "="*70 + "\n")
