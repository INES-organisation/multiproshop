"""
Script pour mapper les produits CJ vers les catégories MPS françaises
Utilise les catégories CJ existantes des produits pour les mapper vers les catégories MPS correspondantes
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from extensions import db
from models.product import Product
from models.category import Category
from sqlalchemy import func

def get_category_mapping():
    """Mapping manuel des catégories CJ vers MPS basé sur les noms"""
    return {
        # Électronique
        'Electronics': 1,  # Électronique & High-Tech
        'Computer': 1,
        'Phone': 1,
        'Tablet': 1,
        'Camera': 1,
        'Audio': 7,  # Audio & Sono
        'Headphone': 9,  # Casques audio
        'Speaker': 8,  # Enceintes Bluetooth
        
        # Mode
        'Fashion': 13,  # Mode & Vêtements
        'Clothing': 13,
        'Men': 14,  # Mode Homme
        'Women': 15,  # Mode Femme
        'Shoes': 19,  # Chaussures
        'Bag': 20,  # Sacs & Bagages
        'Watch': 21,  # Montres
        'Jewelry': 22,  # Bijoux & Accessoires
        
        # Maison
        'Home': 23,  # Maison & Jardin
        'Kitchen': 24,  # Cuisine & Maison
        'Furniture': 25,  # Meubles
        'Garden': 26,  # Jardin & Extérieur
        'Decoration': 27,  # Décoration
        
        # Sport
        'Sport': 28,  # Sports & Loisirs
        'Fitness': 29,  # Fitness & Musculation
        'Outdoor': 30,  # Sports d\'extérieur
        
        # Beauté
        'Beauty': 31,  # Beauté & Santé
        'Makeup': 32,  # Maquillage
        'Skincare': 33,  # Soins de la peau
        'Hair': 34,  # Soins des cheveux
        
        # Jouets
        'Toy': 35,  # Jouets & Enfants
        'Baby': 36,  # Bébé & Puériculture
        'Kids': 37,  # Enfants
        
        # Auto
        'Auto': 38,  # Auto & Moto
        'Car': 38,
        'Motorcycle': 39,  # Moto & Scooter
        
        # Animaux
        'Pet': 40,  # Animaux de compagnie
        'Dog': 41,  # Chiens
        'Cat': 42,  # Chats
    }

def find_best_mps_category(cj_category_name):
    """Trouver la meilleure catégorie MPS pour une catégorie CJ"""
    mapping = get_category_mapping()
    
    if not cj_category_name:
        return 1  # Par défaut: Électronique & High-Tech
    
    # Recherche exacte
    for key, mps_id in mapping.items():
        if key.lower() in cj_category_name.lower():
            return mps_id
    
    # Par défaut
    return 1

def map_products_to_mps_categories():
    """Mapper tous les produits CJ vers les catégories MPS"""
    app = create_app()
    
    with app.app_context():
        print("\n" + "="*80)
        print("MAPPING DES PRODUITS CJ VERS LES CATÉGORIES MPS")
        print("="*80 + "\n")
        
        # Récupérer tous les produits CJ
        cj_products = Product.query.filter(Product.cj_pid.isnot(None)).all()
        print(f"Produits CJ à mapper: {len(cj_products)}")
        
        # Récupérer les catégories CJ uniques
        cj_categories = db.session.query(
            Category.id,
            Category.name,
            func.count(Product.id).label('product_count')
        ).join(Product).filter(
            Product.cj_pid.isnot(None)
        ).group_by(Category.id, Category.name).all()
        
        print(f"\nCatégories CJ avec produits: {len(cj_categories)}")
        
        # Statistiques
        mapped_count = 0
        category_stats = {}
        
        # Mapper chaque produit
        for product in cj_products:
            if product.category:
                cj_cat_name = product.category.name
                
                # Trouver la catégorie MPS correspondante
                mps_category_id = find_best_mps_category(cj_cat_name)
                
                # Mettre à jour le produit
                product.category_id = mps_category_id
                
                # Stats
                if mps_category_id not in category_stats:
                    category_stats[mps_category_id] = 0
                category_stats[mps_category_id] += 1
                
                mapped_count += 1
                
                if mapped_count % 1000 == 0:
                    print(f"  Mappé: {mapped_count}/{len(cj_products)} produits...")
                    db.session.commit()
        
        # Commit final
        db.session.commit()
        
        print(f"\n✅ Mapping terminé: {mapped_count} produits mappés")
        
        # Afficher les statistiques
        print("\n" + "="*80)
        print("STATISTIQUES PAR CATÉGORIE MPS")
        print("="*80 + "\n")
        
        for cat_id, count in sorted(category_stats.items(), key=lambda x: x[1], reverse=True)[:20]:
            cat = Category.query.get(cat_id)
            if cat:
                print(f"  {cat.name:50} : {count:6} produits")
        
        print("\n" + "="*80)
        print("✅ MAPPING TERMINÉ AVEC SUCCÈS")
        print("="*80 + "\n")

if __name__ == '__main__':
    map_products_to_mps_categories()
