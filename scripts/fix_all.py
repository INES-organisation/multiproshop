import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from extensions import db
from models.api_provider import CategoryMapping

# Traductions directes SQL
REPLACEMENTS = [
    ('Woman', 'Femme'), ('Man', 'Homme'), ('Men', 'Hommes'), ('Women', 'Femmes'),
    ('Ladies', 'Dames'), ('Mens', 'Hommes'), ('Womens', 'Femmes'),
    ('Kids', 'Enfants'), ('Baby', 'Bebe'), ('Girl', 'Fille'), ('Boy', 'Garcon'),
    ('Girls', 'Filles'), ('Boys', 'Garcons'), ('Children', 'Enfants'),
    ('Clothing', 'Vetements'), ('Tops', 'Hauts'), ('Bottoms', 'Bas'),
    ('Dresses', 'Robes'), ('Skirts', 'Jupes'), ('Pants', 'Pantalons'),
    ('Suits', 'Costumes'), ('Sets', 'Ensembles'), ('Coats', 'Manteaux'),
    ('Jackets', 'Vestes'), ('Sweaters', 'Pulls'), ('Hoodies', 'Sweats a capuche'),
    ('Sweatshirts', 'Sweatshirts'), ('Shirts', 'Chemises'), ('Blouses', 'Chemisiers'),
    ('T-Shirts', 'T-shirts'), ('Underwear', 'Sous-vetements'), ('Intimates', 'Lingerie'),
    ('Sleepwear', 'Vetements de nuit'), ('Loungewear', 'Vetements d\'interieur'),
    ('Pajamas', 'Pyjamas'), ('Pajama', 'Pyjama'), ('Robes', 'Peignoirs'),
    ('Shoes', 'Chaussures'), ('Boots', 'Bottes'), ('Sneakers', 'Baskets'),
    ('Sandals', 'Sandales'), ('Heels', 'Talons'), ('Flats', 'Plates'),
    ('Slippers', 'Pantoufles'), ('Running', 'Course'), ('Dance', 'Danse'),
    ('Hiking', 'Randonnee'), ('Soccer', 'Football'), ('Basketball', 'Basket'),
    ('Bags', 'Sacs'), ('Backpacks', 'Sacs a dos'), ('Wallets', 'Portefeuilles'),
    ('Handbags', 'Sacs a main'), ('Crossbody', 'Bandouliere'), ('Shoulder', 'Epaule'),
    ('Evening', 'Soiree'), ('Fashion', 'Mode'), ('School', 'Ecole'),
    ('Belts', 'Ceintures'), ('Hats', 'Chapeaux'), ('Caps', 'Casquettes'),
    ('Scarves', 'Echarpes'), ('Wraps', 'Foulards'), ('Gloves', 'Gants'),
    ('Mittens', 'Moufles'), ('Socks', 'Chaussettes'), ('Watches', 'Montres'),
    ('Sunglasses', 'Lunettes de soleil'), ('Eyewear', 'Lunettes'),
    ('Prescription', 'Vue'), ('Accessories', 'Accessoires'),
    ('Jewelry', 'Bijoux'), ('Necklaces', 'Colliers'), ('Earrings', 'Boucles d\'oreilles'),
    ('Rings', 'Bagues'), ('Bracelets', 'Bracelets'),
    ('Sports', 'Sports'), ('Outdoor', 'Plein air'), ('Cycling', 'Cyclisme'),
    ('Swimming', 'Natation'), ('Jerseys', 'Maillots'), ('Swimwear', 'Maillots de bain'),
    ('Bikini', 'Bikini'), ('One-Piece', 'Une piece'), ('Two-Piece', 'Deux pieces'),
    ('Phone', 'Telephone'), ('Computer', 'Ordinateur'), ('Laptop', 'Portable'),
    ('Tablet', 'Tablette'), ('Camera', 'Appareil photo'), ('Smart', 'Intelligent'),
    ('Home', 'Maison'), ('Kitchen', 'Cuisine'), ('Tools', 'Outils'),
    ('Hand', 'Manuel'), ('Power', 'Electrique'), ('Vehicle', 'Vehicule'),
    ('Car', 'Voiture'), ('Motorcycle', 'Moto'), ('Seat', 'Siege'),
    ('Other', 'Autre'), ('Case', 'Etui'), ('Cases', 'Etuis'),
    ('Office', 'Bureau'), ('Face', 'Visage'), ('Masks', 'Masques'),
    ('Couple', 'Couple'), ('Parent-Child', 'Parent-Enfant'),
    ('Long-Sleeves', 'Manches longues'), ('Short-Sleeves', 'Manches courtes'),
    ('Long Sleeve', 'Manches longues'), ('Short Sleeve', 'Manches courtes'),
    ('Sleeve', 'Manche'), ('Sleeves', 'Manches'),
    ('Rompers', 'Barboteuses'), ('Jeans', 'Jeans'), ('Cargo', 'Cargo'),
    ('Harem', 'Sarouel'), ('Casual', 'Decontracte'), ('Formal', 'Formel'),
    ('Baseball', 'Baseball'), ('Bomber', 'Bomber'), ('Waist', 'Ceinture'),
    ('Vulcanize', 'Vulcanise'), ('Skateboarding', 'Skate'),
    ('Supplies', 'Fournitures'), ('Garden', 'Jardin'), ('Storage', 'Rangement'),
    ('Lighting', 'Eclairage'), ('SIM', 'SIM'), ('Printer', 'Imprimante'),
    ('Safety', 'Securite'), ('Workplace', 'Lieu de travail'),
    ('Covers', 'Housses'), ('Key', 'Cle'), ('Call', 'Appel'),
    ('Gear', 'Equipement'), ('Parts', 'Pieces'), ('Audio', 'Audio'),
    ('Video', 'Video'), ('Digital', 'Numerique'), ('Networking', 'Reseau'),
]

with app.app_context():
    print("\n" + "="*80)
    print("TRADUCTION RAPIDE DES CATEGORIES CJ")
    print("="*80 + "\n")
    
    mappings = CategoryMapping.query.filter_by(provider_id=1).all()
    count = 0
    
    for m in mappings:
        original = m.external_category_name
        translated = original
        
        for en, fr in REPLACEMENTS:
            translated = translated.replace(en, fr)
        
        if translated != original:
            m.external_category_name = translated
            count += 1
    
    db.session.commit()
    print(f"✓ {count} categories traduites\n")
    
    # Afficher quelques exemples
    print("Exemples de categories traduites:")
    for m in mappings[:10]:
        print(f"  - {m.external_category_name}")
    
    print("\n" + "="*80)
    print("TERMINE")
    print("="*80 + "\n")
