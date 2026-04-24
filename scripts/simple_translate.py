import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from extensions import db
from models.api_provider import CategoryMapping

# Dictionnaire de traduction complet
TRANS = {
    # Genres et ages
    'Woman': 'Femme', 'Man': 'Homme', 'Men': 'Hommes', 'Women': 'Femmes',
    'Kids': 'Enfants', 'Baby': 'Bebe', 'Girl': 'Fille', 'Boy': 'Garcon',
    'Girls': 'Filles', 'Boys': 'Garcons', 'Children': 'Enfants',
    'Unisex': 'Mixte', 'Adult': 'Adulte', 'Youth': 'Jeune',
    
    # Vetements
    'Clothing': 'Vetements', 'Tops': 'Hauts', 'Bottoms': 'Bas', 
    'Dresses': 'Robes', 'Skirts': 'Jupes', 'Pants': 'Pantalons',
    'Shorts': 'Shorts', 'Suits': 'Costumes', 'Sets': 'Ensembles',
    'Coats': 'Manteaux', 'Jackets': 'Vestes', 'Sweaters': 'Pulls',
    'Hoodies': 'Sweats a capuche', 'Sweatshirts': 'Sweatshirts',
    'Shirts': 'Chemises', 'Blouses': 'Chemisiers', 'T-Shirts': 'T-shirts',
    'Tank': 'Debardeur', 'Tees': 'T-shirts', 'Polo': 'Polo',
    'Jeans': 'Jeans', 'Leggings': 'Leggings', 'Joggers': 'Joggings',
    'Cargo': 'Cargo', 'Harem': 'Sarouel', 'Casual': 'Decontracte',
    'Formal': 'Formel', 'Business': 'Professionnel', 'Sport': 'Sport',
    
    # Sous-vetements et nuit
    'Underwear': 'Sous-vetements', 'Intimates': 'Lingerie',
    'Sleepwear': 'Vetements de nuit', 'Loungewear': 'Vetements d\'interieur',
    'Pajamas': 'Pyjamas', 'Pajama': 'Pyjama', 'Robes': 'Peignoirs',
    'Nightgowns': 'Chemises de nuit', 'Bras': 'Soutiens-gorge',
    
    # Chaussures
    'Shoes': 'Chaussures', 'Boots': 'Bottes', 'Sneakers': 'Baskets',
    'Sandals': 'Sandales', 'Heels': 'Talons', 'Flats': 'Plates',
    'Slippers': 'Pantoufles', 'Loafers': 'Mocassins', 'Oxfords': 'Richelieu',
    'Running': 'Course', 'Dance': 'Danse', 'Skateboarding': 'Skate',
    'Hiking': 'Randonnee', 'Soccer': 'Football', 'Basketball': 'Basket',
    'Vulcanize': 'Vulcanise', 'Athletic': 'Athletique',
    
    # Sacs et accessoires
    'Bags': 'Sacs', 'Backpacks': 'Sacs a dos', 'Wallets': 'Portefeuilles',
    'Handbags': 'Sacs a main', 'Crossbody': 'Bandouliere', 'Shoulder': 'Epaule',
    'Evening': 'Soiree', 'Fashion': 'Mode', 'School': 'Ecole',
    'Waist': 'Ceinture', 'Clutches': 'Pochettes', 'Totes': 'Cabas',
    'Carriers': 'Porte-bebes', 'Luggage': 'Bagages', 'Travel': 'Voyage',
    
    # Accessoires de mode
    'Belts': 'Ceintures', 'Hats': 'Chapeaux', 'Caps': 'Casquettes',
    'Scarves': 'Echarpes', 'Wraps': 'Foulards', 'Gloves': 'Gants',
    'Mittens': 'Moufles', 'Socks': 'Chaussettes', 'Watches': 'Montres',
    'Sunglasses': 'Lunettes de soleil', 'Eyewear': 'Lunettes',
    'Prescription': 'Vue', 'Baseball': 'Baseball', 'Bomber': 'Bomber',
    'Accessories': 'Accessoires', 'Cummerbunds': 'Ceinturons',
    'Hosiery': 'Collants', 'Ties': 'Cravates', 'Bow': 'Noeud',
    
    # Bijoux
    'Jewelry': 'Bijoux', 'Necklaces': 'Colliers', 'Earrings': 'Boucles d\'oreilles',
    'Rings': 'Bagues', 'Bracelets': 'Bracelets', 'Bangles': 'Joncs',
    'Pendants': 'Pendentifs', 'Chains': 'Chaines', 'Charms': 'Breloques',
    
    # Sports et activites
    'Sports': 'Sports', 'Outdoor': 'Plein air', 'Fitness': 'Fitness',
    'Cycling': 'Cyclisme', 'Swimming': 'Natation', 'Yoga': 'Yoga',
    'Jerseys': 'Maillots', 'Swimwear': 'Maillots de bain', 'Bikini': 'Bikini',
    'One-Piece': 'Une piece', 'Two-Piece': 'Deux pieces',
    
    # Electronique et tech
    'Electronics': 'Electronique', 'Phone': 'Telephone', 'Computer': 'Ordinateur',
    'Laptop': 'Ordinateur portable', 'Tablet': 'Tablette', 'Camera': 'Appareil photo',
    'Smart': 'Intelligent', 'Wearable': 'Portable', 'Digital': 'Numerique',
    'Audio': 'Audio', 'Video': 'Video', 'Drones': 'Drones',
    'DVR': 'Enregistreur', 'Dash': 'Tableau de bord', 'SIM': 'SIM',
    'Networking': 'Reseau', 'Printer': 'Imprimante',
    
    # Maison et jardin
    'Home': 'Maison', 'Garden': 'Jardin', 'Kitchen': 'Cuisine',
    'Appliances': 'Electromenager', 'Furniture': 'Meubles',
    'Lighting': 'Eclairage', 'Storage': 'Rangement', 'Decor': 'Decoration',
    'Bedding': 'Literie', 'Bath': 'Salle de bain', 'Dining': 'Salle a manger',
    
    # Outils et equipement
    'Tools': 'Outils', 'Hand': 'Manuel', 'Power': 'Electrique',
    'Welding': 'Soudure', 'Soldering': 'Brasage', 'Machine': 'Machine',
    'Diagnostic': 'Diagnostic', 'Supplies': 'Fournitures',
    'Safety': 'Securite', 'Workplace': 'Lieu de travail',
    
    # Automobile et moto
    'Vehicle': 'Vehicule', 'Car': 'Voiture', 'Motorcycle': 'Moto',
    'Moto': 'Moto', 'Exterior': 'Exterieur', 'Interior': 'Interieur',
    'Seat': 'Siege', 'Covers': 'Housses', 'Key': 'Cle',
    
    # Mots de liaison et autres
    'and': 'et', '&': '&', 'for': 'pour', 'with': 'avec',
    'Other': 'Autre', 'Others': 'Autres', 'Case': 'Etui',
    'Cases': 'Etuis', 'Gear': 'Equipement', 'Parts': 'Pieces',
    'Call': 'Appel', 'Office': 'Bureau', 'Outerwear': 'Exterieurs',
    'Face': 'Visage', 'Masks': 'Masques', 'Couple': 'Couple',
    'Parent-Child': 'Parent-Enfant', 'Long-Sleeves': 'Manches longues',
    'Short-Sleeves': 'Manches courtes', 'Couple&Parent-Child': 'Couple et Parent-Enfant',
    'Rompers': 'Barboteuses', 'Peignoirs': 'Peignoirs',
}

with app.app_context():
    mappings = CategoryMapping.query.filter_by(provider_id=1).all()
    count = 0
    
    for m in mappings:
        original = m.external_category_name
        translated = original
        
        for en, fr in TRANS.items():
            translated = translated.replace(en, fr)
        
        if translated != original:
            m.external_category_name = translated
            count += 1
    
    db.session.commit()
    print(f"TERMINE: {count} categories traduites")
