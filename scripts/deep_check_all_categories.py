"""
Script pour vérifier EN PROFONDEUR toutes les catégories principales
et identifier TOUTES les incohérences
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.product import Product
from models.category import Category

app = create_app()

with app.app_context():
    # Toutes les catégories principales MPS
    main_categories = [
        ('Électronique & High-Tech', 1),
        ('Informatique', 22),
        ('Téléphonie & Tablettes', 38),
        ('Mode & Vêtements', 52),
        ('Maison & Jardin', 67),
        ('Santé & Beauté', 87),
        ('Sports & Loisirs', 100),
        ('Bébés & Puériculture', 113),
        ('Jeux & Jouets', 126),
        ('Auto & Moto', 139),
        ('Bricolage & Outillage', 152),
        ('Alimentation & Boissons', 165),
        ('Animalerie', 178),
    ]
    
    print("\n" + "="*100)
    print("VÉRIFICATION APPROFONDIE DE TOUTES LES CATÉGORIES")
    print("="*100 + "\n")
    
    for cat_name, cat_id in main_categories:
        cat = Category.query.get(cat_id)
        if not cat:
            continue
        
        prods = Product.query.filter_by(category_id=cat_id).limit(30).all()
        total = Product.query.filter_by(category_id=cat_id).count()
        
        print(f"\n{'='*100}")
        print(f"📦 Catégorie: {cat_name} (ID: {cat_id})")
        print(f"   Total produits: {total}")
        print(f"{'='*100}\n")
        
        if total == 0:
            print("   ⚠️ Aucun produit\n")
            continue
        
        for i, p in enumerate(prods, 1):
            print(f"{i:2}. {p.name[:90]}")
        
        print()
