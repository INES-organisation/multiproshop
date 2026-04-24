"""
Débugger les catégories et la synchronisation
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from app import create_app
from models.product import Product
from models.category import Category
from extensions import db

app = create_app()

with app.app_context():
    print("\n" + "="*70)
    print("DEBUG CATÉGORIES ET SYNCHRONISATION")
    print("="*70 + "\n")
    
    # Vérifier la catégorie "Boy Accessories"
    print("1. Recherche catégorie 'Boy Accessories'...")
    boy_acc = Category.query.filter(Category.name.like('%Boy Accessories%')).all()
    
    if boy_acc:
        for cat in boy_acc:
            print(f"\n   Trouvée: {cat.name}")
            print(f"   ID: {cat.id}")
            print(f"   CJ Category ID: {cat.cj_category_id}")
            print(f"   Niveau: {cat.level}")
            print(f"   Visible: {cat.visible}")
            
            # Compter les produits
            products = Product.query.filter_by(category_id=cat.id).count()
            products_cj = Product.query.filter(
                Product.category_id == cat.id,
                Product.cj_pid.isnot(None)
            ).count()
            
            print(f"   Produits totaux: {products}")
            print(f"   Produits CJ (avec cj_pid): {products_cj}")
    else:
        print("   ✗ Aucune catégorie 'Boy Accessories' trouvée")
    
    # Vérifier Computer Tablet Accessories
    print("\n2. Catégorie 'Computer Tablet Accessories'...")
    comp_tab = Category.query.filter(
        Category.name.like('%Computer Tablet Accessories%')
    ).first()
    
    if comp_tab:
        print(f"   Trouvée: {comp_tab.name}")
        print(f"   CJ Category ID: {comp_tab.cj_category_id}")
        
        products_cj = Product.query.filter(
            Product.category_id == comp_tab.id,
            Product.cj_pid.isnot(None)
        ).count()
        print(f"   Produits CJ: {products_cj}")
    
    # Lister toutes les catégories avec produits CJ
    print("\n3. Toutes les catégories avec produits CJ:")
    
    categories_with_cj = db.session.query(
        Category.id,
        Category.name,
        Category.cj_category_id,
        Category.level,
        db.func.count(Product.id).label('count')
    ).join(
        Product, Product.category_id == Category.id
    ).filter(
        Product.cj_pid.isnot(None)
    ).group_by(Category.id).order_by(db.desc('count')).all()
    
    for cat_id, name, cj_id, level, count in categories_with_cj:
        print(f"\n   {name} (Niveau {level})")
        print(f"   CJ ID: {cj_id}")
        print(f"   Produits CJ: {count}")
    
    # Vérifier les catégories visibles
    print("\n4. Catégories CJ visibles (niveau 3):")
    visible_cats = Category.query.filter(
        Category.cj_category_id.isnot(None),
        Category.level == 3,
        Category.visible == True
    ).count()
    
    print(f"   Total: {visible_cats}")
    
    # Exemples de catégories visibles avec/sans produits
    print("\n5. Exemples catégories visibles:")
    examples = Category.query.filter(
        Category.cj_category_id.isnot(None),
        Category.level == 3,
        Category.visible == True
    ).limit(10).all()
    
    for cat in examples:
        products_count = Product.query.filter(
            Product.category_id == cat.id,
            Product.cj_pid.isnot(None)
        ).count()
        
        print(f"\n   {cat.name}")
        print(f"   CJ ID: {cat.cj_category_id}")
        print(f"   Produits CJ: {products_count}")
    
    print("\n" + "="*70 + "\n")
