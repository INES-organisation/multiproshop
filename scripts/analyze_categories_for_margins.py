"""
Script pour analyser les catégories et proposer des marges intelligentes
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from models.category import Category
from models.product import Product
from sqlalchemy import func

def analyze_categories():
    with app.app_context():
        print("\n" + "="*80)
        print("ANALYSE DES CATÉGORIES POUR MARGES INTELLIGENTES")
        print("="*80 + "\n")
        
        # Récupérer toutes les catégories CJ avec leurs produits
        categories = Category.query.filter(
            Category.cj_category_id.isnot(None)
        ).order_by(Category.level, Category.name).all()
        
        print(f"Total catégories CJ: {len(categories)}\n")
        
        # Grouper par niveau
        by_level = {}
        for cat in categories:
            level = cat.level or 1
            if level not in by_level:
                by_level[level] = []
            by_level[level].append(cat)
        
        # Analyser chaque niveau
        for level in sorted(by_level.keys()):
            cats = by_level[level]
            print(f"\n{'='*80}")
            print(f"NIVEAU {level} - {len(cats)} catégories")
            print('='*80)
            
            # Trier par nombre de produits
            cats_sorted = sorted(cats, key=lambda c: c.product_count or 0, reverse=True)
            
            for cat in cats_sorted[:20]:  # Top 20 par niveau
                product_count = cat.product_count or 0
                if product_count > 0:
                    # Calculer prix moyen
                    avg_price = Product.query.filter_by(
                        category_id=cat.id
                    ).with_entities(
                        func.avg(Product.cost_price)
                    ).scalar()
                    
                    avg_price = avg_price or 0
                    
                    print(f"\n{cat.name[:50]:<50} | Produits: {product_count:>4} | Prix moy: ${avg_price:.2f}")
                    print(f"  ID: {cat.id} | CJ ID: {cat.cj_category_id}")
        
        print("\n" + "="*80)
        print("RECOMMANDATIONS DE MARGES PAR TYPE DE PRODUIT")
        print("="*80 + "\n")
        
        recommendations = {
            "Électronique & High-Tech": {
                "margin": 40,
                "reason": "Marché compétitif, prix sensibles",
                "categories": ["Computer", "Electronics", "Phone", "Tablet", "Laptop"]
            },
            "Mode & Accessoires": {
                "margin": 70,
                "reason": "Forte valeur perçue, moins de comparaison",
                "categories": ["Clothing", "Fashion", "Shoes", "Bags", "Watches"]
            },
            "Maison & Jardin": {
                "margin": 60,
                "reason": "Équilibre qualité/prix",
                "categories": ["Home", "Garden", "Furniture", "Kitchen", "Decor"]
            },
            "Bijoux & Montres": {
                "margin": 90,
                "reason": "Très forte valeur perçue",
                "categories": ["Jewelry", "Watches", "Accessories"]
            },
            "Jouets & Enfants": {
                "margin": 55,
                "reason": "Volume important, prix moyens",
                "categories": ["Toys", "Kids", "Baby", "Children"]
            },
            "Sport & Outdoor": {
                "margin": 60,
                "reason": "Qualité importante",
                "categories": ["Sports", "Outdoor", "Fitness", "Camping"]
            },
            "Beauté & Santé": {
                "margin": 70,
                "reason": "Forte valeur perçue",
                "categories": ["Beauty", "Health", "Hair", "Cosmetics"]
            },
            "Auto & Moto": {
                "margin": 50,
                "reason": "Produits techniques",
                "categories": ["Auto", "Motorcycle", "Car", "Vehicle"]
            },
            "Animaux": {
                "margin": 60,
                "reason": "Marché de niche",
                "categories": ["Pet", "Dog", "Cat", "Animal"]
            },
            "Autres": {
                "margin": 60,
                "reason": "Marge par défaut",
                "categories": []
            }
        }
        
        for category_type, info in recommendations.items():
            print(f"\n{category_type}")
            print(f"  Marge recommandée: {info['margin']}%")
            print(f"  Raison: {info['reason']}")
            if info['categories']:
                print(f"  Mots-clés: {', '.join(info['categories'][:5])}")

if __name__ == '__main__':
    analyze_categories()
