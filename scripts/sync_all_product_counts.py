"""
Synchroniser tous les compteurs de produits du site
- Compteurs de catégories (product_count)
- Statistiques globales
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
    print("SYNCHRONISATION DES COMPTEURS DE PRODUITS")
    print("="*70 + "\n")
    
    # 1. Statistiques globales
    print("1. STATISTIQUES GLOBALES")
    print("-" * 70)
    
    total_products = Product.query.count()
    active_products = Product.query.filter_by(is_active=True).count()
    published_products = Product.query.filter_by(published=True).count()
    cj_products = Product.query.filter(Product.cj_pid.isnot(None)).count()
    
    print(f"Total produits: {total_products}")
    print(f"  - Actifs: {active_products}")
    print(f"  - Publiés: {published_products}")
    print(f"  - Produits CJ (avec cj_pid): {cj_products}")
    
    # 2. Mise à jour des compteurs de catégories
    print("\n2. MISE À JOUR DES COMPTEURS DE CATÉGORIES")
    print("-" * 70)
    
    all_categories = Category.query.all()
    updated_count = 0
    categories_with_products = 0
    
    for cat in all_categories:
        # Compter TOUS les produits actifs dans cette catégorie
        count = Product.query.filter(
            Product.category_id == cat.id,
            Product.is_active == True
        ).count()
        
        if cat.product_count != count:
            cat.product_count = count
            updated_count += 1
        
        if count > 0:
            categories_with_products += 1
    
    db.session.commit()
    
    print(f"✓ {updated_count} catégories mises à jour")
    print(f"✓ {categories_with_products} catégories avec produits actifs")
    
    # 3. Détails par type de catégorie
    print("\n3. CATÉGORIES PAR TYPE")
    print("-" * 70)
    
    # Catégories CJ
    cj_categories = Category.query.filter(
        Category.cj_category_id.isnot(None)
    ).count()
    
    cj_with_products = Category.query.filter(
        Category.cj_category_id.isnot(None),
        Category.product_count > 0
    ).count()
    
    print(f"Catégories CJ: {cj_categories}")
    print(f"  - Avec produits: {cj_with_products}")
    
    # Catégories non-CJ
    non_cj_categories = Category.query.filter(
        Category.cj_category_id.is_(None)
    ).count()
    
    non_cj_with_products = Category.query.filter(
        Category.cj_category_id.is_(None),
        Category.product_count > 0
    ).count()
    
    print(f"Catégories non-CJ: {non_cj_categories}")
    print(f"  - Avec produits: {non_cj_with_products}")
    
    # 4. Top 10 catégories avec le plus de produits
    print("\n4. TOP 10 CATÉGORIES (PRODUITS ACTIFS)")
    print("-" * 70)
    
    top_categories = Category.query.filter(
        Category.product_count > 0
    ).order_by(Category.product_count.desc()).limit(10).all()
    
    for i, cat in enumerate(top_categories, 1):
        cj_marker = "🔵 CJ" if cat.cj_category_id else "⚪ Local"
        print(f"{i:2}. {cj_marker} {cat.name[:50]:50} : {cat.product_count:3} produits")
    
    # 5. Vérification cohérence
    print("\n5. VÉRIFICATION COHÉRENCE")
    print("-" * 70)
    
    # Somme des compteurs de catégories niveau 3
    level3_sum = db.session.query(
        db.func.sum(Category.product_count)
    ).filter(Category.level == 3).scalar() or 0
    
    print(f"Somme compteurs catégories niveau 3: {level3_sum}")
    print(f"Total produits actifs: {active_products}")
    
    if level3_sum != active_products:
        print(f"⚠️  ATTENTION: Différence de {abs(level3_sum - active_products)} produits")
        print("   Cela peut être normal si des produits n'ont pas de catégorie niveau 3")
        
        # Compter les produits sans catégorie ou dans catégories non-niveau-3
        products_no_cat = Product.query.filter(
            Product.is_active == True,
            Product.category_id.is_(None)
        ).count()
        
        products_not_level3 = db.session.query(Product).join(
            Category, Product.category_id == Category.id
        ).filter(
            Product.is_active == True,
            Category.level != 3
        ).count()
        
        print(f"   - Produits sans catégorie: {products_no_cat}")
        print(f"   - Produits dans catégories non-niveau-3: {products_not_level3}")
    else:
        print("✓ Cohérence parfaite !")
    
    # 6. Résumé final
    print("\n" + "="*70)
    print("RÉSUMÉ FINAL")
    print("="*70)
    print(f"Total produits: {total_products}")
    print(f"Produits actifs: {active_products}")
    print(f"Produits publiés: {published_products}")
    print(f"Produits CJ: {cj_products}")
    print(f"Catégories totales: {len(all_categories)}")
    print(f"Catégories avec produits: {categories_with_products}")
    print(f"Compteurs mis à jour: {updated_count}")
    print("="*70 + "\n")
