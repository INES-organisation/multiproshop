"""
Script de traduction automatique des catégories CJ Dropshipping
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from extensions import db
from models.api_provider import CategoryMapping
import re

def translate_category_name(english_name):
    """Traduire un nom de catégorie de l'anglais vers le français"""
    
    # Dictionnaire de traduction des mots courants
    translations = {
        # Genres
        'Woman': 'Femme',
        'Man': 'Homme',
        'Men': 'Hommes',
        'Women': 'Femmes',
        'Kids': 'Enfants',
        'Baby': 'Bébé',
        'Girl': 'Fille',
        'Boy': 'Garçon',
        'Unisex': 'Mixte',
        
        # Vêtements
        'Clothing': 'Vêtements',
        'Tops': 'Hauts',
        'Bottoms': 'Bas',
        'Dresses': 'Robes',
        'Skirts': 'Jupes',
        'Pants': 'Pantalons',
        'Jeans': 'Jeans',
        'Shorts': 'Shorts',
        'Leggings': 'Leggings',
        'Suits': 'Costumes',
        'Sets': 'Ensembles',
        'Outerwear': 'Vêtements d\'extérieur',
        'Coats': 'Manteaux',
        'Jackets': 'Vestes',
        'Sweaters': 'Pulls',
        'Hoodies': 'Sweats à capuche',
        'Sweatshirts': 'Sweatshirts',
        'T-Shirts': 'T-shirts',
        'Shirts': 'Chemises',
        'Blouses': 'Chemisiers',
        'Tank Tops': 'Débardeurs',
        'Cardigans': 'Cardigans',
        'Vests': 'Gilets',
        'Blazers': 'Blazers',
        
        # Sous-vêtements et nuit
        'Underwear': 'Sous-vêtements',
        'Intimates': 'Lingerie',
        'Bras': 'Soutiens-gorge',
        'Panties': 'Culottes',
        'Sleepwear': 'Vêtements de nuit',
        'Loungewear': 'Vêtements d\'intérieur',
        'Pajamas': 'Pyjamas',
        'Robes': 'Peignoirs',
        'Nightgowns': 'Chemises de nuit',
        
        # Chaussures
        'Shoes': 'Chaussures',
        'Boots': 'Bottes',
        'Sneakers': 'Baskets',
        'Sandals': 'Sandales',
        'Slippers': 'Pantoufles',
        'Heels': 'Talons',
        'Flats': 'Chaussures plates',
        'Loafers': 'Mocassins',
        'Oxfords': 'Richelieu',
        
        # Accessoires
        'Accessories': 'Accessoires',
        'Bags': 'Sacs',
        'Handbags': 'Sacs à main',
        'Backpacks': 'Sacs à dos',
        'Wallets': 'Portefeuilles',
        'Belts': 'Ceintures',
        'Hats': 'Chapeaux',
        'Caps': 'Casquettes',
        'Scarves': 'Écharpes',
        'Wraps': 'Foulards',
        'Gloves': 'Gants',
        'Mittens': 'Moufles',
        'Socks': 'Chaussettes',
        'Hosiery': 'Collants',
        'Sunglasses': 'Lunettes de soleil',
        'Eyewear': 'Lunettes',
        'Watches': 'Montres',
        
        # Bijoux
        'Jewelry': 'Bijoux',
        'Necklaces': 'Colliers',
        'Pendants': 'Pendentifs',
        'Earrings': 'Boucles d\'oreilles',
        'Rings': 'Bagues',
        'Bracelets': 'Bracelets',
        'Bangles': 'Bracelets rigides',
        'Anklets': 'Bracelets de cheville',
        'Brooches': 'Broches',
        
        # Beauté et santé
        'Beauty': 'Beauté',
        'Health': 'Santé',
        'Makeup': 'Maquillage',
        'Skin Care': 'Soins de la peau',
        'Hair Care': 'Soins des cheveux',
        'Nail': 'Ongles',
        'Perfume': 'Parfum',
        'Fragrances': 'Parfums',
        
        # Maison
        'Home': 'Maison',
        'Garden': 'Jardin',
        'Decor': 'Décoration',
        'Kitchen': 'Cuisine',
        'Dining': 'Salle à manger',
        'Bedding': 'Literie',
        'Bath': 'Salle de bain',
        'Storage': 'Rangement',
        'Organization': 'Organisation',
        'Furniture': 'Meubles',
        'Lighting': 'Éclairage',
        
        # Électronique
        'Electronics': 'Électronique',
        'Phone': 'Téléphone',
        'Computer': 'Ordinateur',
        'Office': 'Bureau',
        'Camera': 'Appareil photo',
        
        # Sports
        'Sports': 'Sports',
        'Entertainment': 'Loisirs',
        'Fitness': 'Fitness',
        'Outdoor': 'Plein air',
        'Cycling': 'Cyclisme',
        'Swimming': 'Natation',
        'Running': 'Course',
        'Yoga': 'Yoga',
        
        # Autres
        'Toys': 'Jouets',
        'Hobbies': 'Loisirs',
        'Pet': 'Animal',
        'Supplies': 'Fournitures',
        'Tools': 'Outils',
        'Automotive': 'Automobile',
        'Motorcycle': 'Moto',
        'Travel': 'Voyage',
        'Luggage': 'Bagages',
        
        # Mots de liaison
        'and': 'et',
        'for': 'pour',
        'with': 'avec',
        '&': '&',
        'the': 'le/la',
    }
    
    # Traduction mot par mot
    words = re.split(r'([&\s-]+)', english_name)
    translated_words = []
    
    for word in words:
        if word.strip() in ['&', '-', ' ', '']:
            translated_words.append(word)
        elif word in translations:
            translated_words.append(translations[word])
        else:
            # Garder le mot original si pas de traduction
            translated_words.append(word)
    
    return ''.join(translated_words)

def main():
    """Traduire toutes les catégories CJ"""
    with app.app_context():
        mappings = CategoryMapping.query.filter_by(provider_id=1).all()
        
        print("\n" + "="*80)
        print("TRADUCTION AUTOMATIQUE DES CATEGORIES CJ DROPSHIPPING")
        print("="*80 + "\n")
        
        translated = 0
        
        for mapping in mappings:
            original_name = mapping.external_category_name
            french_name = translate_category_name(original_name)
            
            if french_name != original_name:
                mapping.external_category_name = french_name
                translated += 1
                print(f"{original_name:50} -> {french_name}")
        
        # Sauvegarder
        db.session.commit()
        
        print("\n" + "="*80)
        print(f"TERMINE: {translated} categories traduites sur {len(mappings)}")
        print("="*80 + "\n")

if __name__ == '__main__':
    main()
