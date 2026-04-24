"""
Script pour corriger le mapping des produits CJ vers les catégories MPS
Utilise la table category_mapping pour mapper correctement les produits
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from extensions import db
from models.product import Product
from models.category import Category
from models.api_provider import CategoryMapping
from sqlalchemy import func

def get_mps_category_for_cj_category(cj_category_id, cj_category_name):
    """Trouver la catégorie MPS correspondante pour une catégorie CJ"""
    
    # 1. Chercher dans la table de mapping
    mapping = CategoryMapping.query.filter_by(
        external_category_id=str(cj_category_id)
    ).first()
    
    if mapping and mapping.mps_category_id:
        return mapping.mps_category_id
    
    # 2. Mapping manuel basé sur les mots-clés dans le nom
    name_lower = cj_category_name.lower()
    
    # Électronique & High-Tech (ID: 1)
    electronics_keywords = ['electronic', 'computer', 'laptop', 'phone', 'tablet', 'camera', 
                           'gaming', 'console', 'headphone', 'speaker', 'audio', 'video',
                           'tv', 'monitor', 'keyboard', 'mouse', 'printer', 'scanner',
                           'drone', 'robot', 'smart', 'tech', 'digital', 'gadget']
    
    # Mode & Vêtements (ID: 13)
    fashion_keywords = ['fashion', 'clothing', 'apparel', 'wear', 'dress', 'shirt', 'pant',
                       'jean', 'jacket', 'coat', 'sweater', 'hoodie', 'skirt', 'suit',
                       'underwear', 'sock', 'tie', 'scarf', 'glove', 'hat', 'cap']
    
    # Chaussures (ID: 19)
    shoes_keywords = ['shoe', 'boot', 'sneaker', 'sandal', 'slipper', 'heel', 'footwear']
    
    # Sacs & Bagages (ID: 20)
    bags_keywords = ['bag', 'backpack', 'luggage', 'suitcase', 'wallet', 'purse', 'handbag']
    
    # Montres (ID: 21)
    watch_keywords = ['watch', 'clock', 'timepiece']
    
    # Bijoux & Accessoires (ID: 22)
    jewelry_keywords = ['jewelry', 'jewellery', 'necklace', 'bracelet', 'ring', 'earring',
                       'pendant', 'accessory', 'accessories']
    
    # Maison & Jardin (ID: 23)
    home_keywords = ['home', 'house', 'living', 'bedroom', 'bathroom', 'kitchen',
                    'furniture', 'decor', 'decoration', 'garden', 'outdoor', 'patio',
                    'lamp', 'light', 'lighting', 'curtain', 'rug', 'carpet', 'pillow']
    
    # Sports & Loisirs (ID: 28)
    sport_keywords = ['sport', 'fitness', 'gym', 'exercise', 'yoga', 'running', 'cycling',
                     'swimming', 'camping', 'hiking', 'fishing', 'hunting', 'outdoor sport']
    
    # Beauté & Santé (ID: 31)
    beauty_keywords = ['beauty', 'cosmetic', 'makeup', 'skincare', 'hair care', 'nail',
                      'perfume', 'fragrance', 'health', 'wellness', 'massage', 'spa']
    
    # Jouets & Enfants (ID: 35)
    toys_keywords = ['toy', 'game', 'puzzle', 'doll', 'action figure', 'lego', 'playset',
                    'kids', 'children', 'baby', 'infant', 'toddler', 'nursery']
    
    # Auto & Moto (ID: 38)
    auto_keywords = ['auto', 'car', 'vehicle', 'motorcycle', 'bike', 'automotive',
                    'tire', 'wheel', 'engine', 'motor']
    
    # Animaux de compagnie (ID: 40)
    pet_keywords = ['pet', 'dog', 'cat', 'bird', 'fish', 'animal', 'aquarium']
    
    # Vérifier les mots-clés
    for keyword in shoes_keywords:
        if keyword in name_lower:
            return 19
    
    for keyword in bags_keywords:
        if keyword in name_lower:
            return 20
    
    for keyword in watch_keywords:
        if keyword in name_lower:
            return 21
    
    for keyword in jewelry_keywords:
        if keyword in name_lower:
            return 22
    
    for keyword in beauty_keywords:
        if keyword in name_lower:
            return 31
    
    for keyword in fashion_keywords:
        if keyword in name_lower:
            return 13
    
    for keyword in home_keywords:
        if keyword in name_lower:
            return 23
    
    for keyword in sport_keywords:
        if keyword in name_lower:
            return 28
    
    for keyword in toys_keywords:
        if keyword in name_lower:
            return 35
    
    for keyword in auto_keywords:
        if keyword in name_lower:
            return 38
    
    for keyword in pet_keywords:
        if keyword in name_lower:
            return 40
    
    for keyword in electronics_keywords:
        if keyword in name_lower:
            return 1
    
    # Par défaut: Électronique & High-Tech
    return 1

def fix_cj_products_mapping():
    """Corriger le mapping des produits CJ vers les catégories MPS"""
    app = create_app()
    
    with app.app_context():
        print("\n" + "="*80)
        print("CORRECTION DU MAPPING DES PRODUITS CJ VERS LES CATÉGORIES MPS")
        print("="*80 + "\n")
        
        # Récupérer tous les produits CJ avec leur catégorie CJ d'origine
        cj_products = db.session.query(
            Product.id,
            Product.name,
            Product.category_id,
            Category.cj_category_id,
            Category.name.label('cj_category_name')
        ).join(Category).filter(
            Product.cj_pid.isnot(None),
            Category.cj_category_id.isnot(None)
        ).all()
        
        print(f"Produits CJ à remapper: {len(cj_products)}")
        
        if len(cj_products) == 0:
            print("\n⚠️ Aucun produit CJ trouvé avec catégorie CJ d'origine")
            print("Les produits ont peut-être déjà été mappés incorrectement.")
            return
        
        # Statistiques
        mapped_count = 0
        category_stats = {}
        
        # Mapper chaque produit
        for prod_id, prod_name, current_cat_id, cj_cat_id, cj_cat_name in cj_products:
            # Trouver la catégorie MPS correspondante
            mps_category_id = get_mps_category_for_cj_category(cj_cat_id, cj_cat_name)
            
            # Mettre à jour le produit
            Product.query.filter_by(id=prod_id).update({'category_id': mps_category_id})
            
            # Stats
            if mps_category_id not in category_stats:
                category_stats[mps_category_id] = 0
            category_stats[mps_category_id] += 1
            
            mapped_count += 1
            
            if mapped_count % 1000 == 0:
                print(f"  Remappé: {mapped_count}/{len(cj_products)} produits...")
                db.session.commit()
        
        # Commit final
        db.session.commit()
        
        print(f"\n✅ Remapping terminé: {mapped_count} produits remappés")
        
        # Afficher les statistiques
        print("\n" + "="*80)
        print("STATISTIQUES PAR CATÉGORIE MPS")
        print("="*80 + "\n")
        
        for cat_id, count in sorted(category_stats.items(), key=lambda x: x[1], reverse=True):
            cat = Category.query.get(cat_id)
            if cat:
                print(f"  {cat.name:50} : {count:6} produits")
        
        print("\n" + "="*80)
        print("✅ REMAPPING TERMINÉ AVEC SUCCÈS")
        print("="*80 + "\n")

if __name__ == '__main__':
    fix_cj_products_mapping()
