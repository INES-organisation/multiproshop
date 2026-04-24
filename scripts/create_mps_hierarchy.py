"""
Création de la hiérarchie MPS 3 niveaux à partir des catégories CJ.
Approche B : Nouvelles catégories MPS L2/L3 avec noms français.

Structure finale :
  MPS L1 (existant) -> MPS L2 (nouveau, traduit FR) -> MPS L3 (nouveau, traduit FR)

Chaque nouvelle catégorie MPS L2/L3 garde une référence vers la catégorie CJ
d'origine via le champ cj_category_id (pour faciliter le mapping futur).
"""
import sys, os, json, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.product import Product
from models.category import Category
from extensions import db

app = create_app()

# ============================================================
# MAPPING CJ L1 -> MPS L1
# ============================================================
CJ_L1_TO_MPS = {
    'Phones & Accessories': 38,
    'Computer & Office': 22,
    'Home, Garden & Furniture': 67,
    "Women's Clothing": 52,
    'Jewelry & Watches': 52,
    "Men's Clothing": 52,
    'Bags & Shoes': 52,
    'Health, Beauty & Hair': 87,
    'Automobiles & Motorcycles': 139,
    'Sports & Outdoors': 100,
    'Home Improvement': 152,
    'Pet Supplies': 178,
    'Consumer Electronics': 1,
    'Toys, Kids & Babies': 126,
}

# ============================================================
# OVERRIDES : certaines CJ L2/L3 doivent aller dans un MPS L1 différent
# ============================================================
CJ_L2_MPS_OVERRIDE = {
    # Sports & Outdoors
    'Swimming': 52,       # Maillots -> Mode
    'Sportswear': 52,     # Vêtements sport -> Mode
    # Toys, Kids & Babies
    'Baby & Mother': 113,     # -> Bébés & Puériculture (MPS)
    'Baby Clothing': 113,     # -> Bébés & Puériculture
    'Boys Clothing': 113,     # -> Bébés & Puériculture
    'Girls Clothing': 113,    # -> Bébés & Puériculture
    # Home, Garden & Furniture
    'LED Lighting': 67,
    'Indoor Lighting': 67,
    'Outdoor Lighting': 67,
}

CJ_L3_MPS_OVERRIDE = {
    'Camping & Hiking': 67,  # -> Maison & Jardin (gazebos, etc.)
}

# ============================================================
# TRADUCTIONS FR des catégories CJ L2
# ============================================================
L2_TRANSLATIONS = {
    # Phones & Accessories
    'Cases & Covers': 'Coques & Étuis',
    'Mobile Phone Accessories': 'Accessoires Téléphone',
    'Mobile Phone Parts': 'Pièces Détachées Téléphone',
    'Mobile Phones': 'Téléphones Mobiles',
    # Computer & Office
    'Computer Peripherals': 'Périphériques Informatiques',
    'Desks & Chairs': 'Bureaux & Chaises',
    'Laptop Accessories': 'Accessoires PC Portable',
    'Laptops & Netbooks': 'PC Portables',
    'Networking': 'Réseau',
    'Office Electronics': 'Électronique de Bureau',
    'Tablets & E-Readers': 'Tablettes & Liseuses',
    # Consumer Electronics
    'Accessories & Parts': 'Accessoires & Pièces',
    'Camera & Photo': 'Photo & Caméra',
    'Home Audio & Video': 'Audio & Vidéo Maison',
    'Portable Audio & Video': 'Audio & Vidéo Portable',
    'Smart Electronics': 'Électronique Intelligente',
    # Home, Garden & Furniture
    'Bathroom Products': 'Salle de Bain',
    'Festive & Party Supplies': 'Fêtes & Événements',
    'Garden Supplies': 'Jardin',
    'Home Decor': 'Décoration Intérieure',
    'Home Storage': 'Rangement & Mobilier',
    'Home Textile': 'Textile Maison',
    'Kitchen, Dining & Bar': 'Cuisine & Arts de la Table',
    # Health, Beauty & Hair
    'Bath & Body': 'Bain & Corps',
    'Hair Care & Styling': 'Soins & Coiffure',
    'Health Care': 'Santé',
    'Makeup': 'Maquillage',
    'Nail Art & Tools': 'Ongles & Manucure',
    'Oral Hygiene': 'Hygiène Bucco-Dentaire',
    'Shaving & Hair Removal': 'Rasage & Épilation',
    'Skin Care': 'Soins de la Peau',
    'Skin Care Tools': 'Outils Soins de la Peau',
    # Women's Clothing
    'Accessories': 'Accessoires Femme',
    'Bottoms': 'Bas Femme',
    'Outerwear & Jackets': 'Vestes & Manteaux Femme',
    'Tops & Sets': 'Hauts & Ensembles Femme',
    # Men's Clothing - on préfixe pour distinguer
    # (géré dynamiquement ci-dessous)
    'Hats & Caps': 'Chapeaux & Casquettes',
    'T-Shirts': 'T-Shirts Homme',
    'Underwear & Loungewear': 'Sous-Vêtements & Détente Homme',
    # Jewelry & Watches
    'Fashion Jewelry': 'Bijoux Fantaisie',
    'Fine Jewelry': 'Bijoux Fins',
    "Men's Watches": 'Montres Homme',
    "Women's Watches": 'Montres Femme',
    'Wedding & Engagement': 'Mariage & Fiançailles',
    # Bags & Shoes
    'Functional Bags': 'Sacs Fonctionnels',
    "Men's Luggage & Bags": 'Bagagerie Homme',
    "Men's Shoes": 'Chaussures Homme',
    'Shoes & Bags': 'Chaussures & Sacs',
    "Women's Luggage & Bags": 'Bagagerie Femme',
    "Women's Shoes": 'Chaussures Femme',
    # Automobiles & Motorcycles
    'Auto Replacement Parts': 'Pièces Auto',
    'Car Electronics': 'Électronique Auto',
    'Exterior Accessories': 'Accessoires Extérieurs',
    'Interior Accessories': 'Accessoires Intérieurs',
    'Motorcycle Accessories & Parts': 'Accessoires Moto',
    # Sports & Outdoors
    'Cycling': 'Cyclisme',
    'Fishing': 'Pêche',
    'Other Sports Equipment': 'Équipement Sportif',
    'Sportswear': 'Vêtements de Sport',
    'Swimming': 'Maillots de Bain',
    # Home Improvement
    'Outdoor Lighting': 'Éclairage Extérieur',
    'Tools': 'Outillage',
    # Pet Supplies
    'Pet Apparels': 'Vêtements Animaux',
    'Pet Bedding': 'Couchage Animaux',
    'Pet Collars, Harnesses & Accessories': 'Colliers & Harnais',
    'Pet Drinking & Feeding': 'Alimentation Animaux',
    'Pet Furnitures': 'Mobilier Animaux',
    'Pet Groomings': 'Toilettage',
    'Pet Outdoor Supplies': 'Plein Air Animaux',
    'Pet Toys': 'Jouets Animaux',
    # Toys, Kids & Babies
    'Baby & Mother': 'Bébé & Maman',
    'Baby Clothing': 'Vêtements Bébé',
    'Boys Clothing': 'Vêtements Garçon',
    'Girls Clothing': 'Vêtements Fille',
    'Toys & Hobbies': 'Jouets & Loisirs Créatifs',
}

# ============================================================
# TRADUCTIONS FR des catégories CJ L3
# ============================================================
L3_TRANSLATIONS = {
    # Phones > Cases & Covers
    'Cases For iPhone 6 & 6 Plus': 'Coques iPhone 6/6 Plus',
    'Cases For iPhone 7 & 7 Plus': 'Coques iPhone 7/7 Plus',
    'Cases For iPhone 8 & 8 Plus': 'Coques iPhone 8/8 Plus',
    'Flip Cases': 'Étuis à Rabat',
    'Galaxy S7 Cases': 'Coques Galaxy S7',
    'Galaxy S8 Cases': 'Coques Galaxy S8',
    'Huawei Cases': 'Coques Huawei',
    'IPhone X Cases': 'Coques iPhone X',
    'Leather Cases': 'Coques en Cuir',
    'Patterned Cases': 'Coques à Motifs',
    'Silicone Cases': 'Coques en Silicone',
    'Wallet Cases': 'Coques Portefeuille',
    'Waterptoof Cases': 'Coques Étanches',
    'Xiaomi Cases': 'Coques Xiaomi',
    # Phones > Accessories
    'Cables': 'Câbles',
    'Chargers': 'Chargeurs',
    'Holders & Stands': 'Supports & Fixations',
    'Lenses': 'Objectifs Photo',
    'Power Bank': 'Batteries Externes',
    'Screen Protectors': 'Protections Écran',
    # Phones > Parts
    'Flex Cables': 'Nappes Flex',
    'Housings': 'Coques Arrière',
    'LCDs': 'Écrans LCD',
    'Mobile Batteries': 'Batteries',
    'SIM Card & Tools': 'Cartes SIM & Outils',
    'Touch Panel': 'Dalles Tactiles',
    # Phones > Mobile Phones
    '3GB RAM': '3 Go RAM',
    '5-inch Display': 'Écran 5 Pouces',
    'Dual SIM Card': 'Double SIM',
    'Octa Core': 'Octa Core',
    'Quad Core': 'Quad Core',
    'Single SIM Card': 'Simple SIM',
    # Computer > Peripherals
    'Computer Cables & Connectors': 'Câbles & Connecteurs',
    'Keyboards': 'Claviers',
    'Mice & Keyboards': 'Souris & Claviers',
    'Mouse Pads': 'Tapis de Souris',
    'USB Gadgets': 'Gadgets USB',
    'Webcams': 'Webcams',
    # Computer > Desks & Chairs
    'Computer Desks': 'Bureaux Informatiques',
    'Office Chairs': 'Chaises de Bureau',
    # Computer > Laptop Accessories
    'Laptop Bags & Cases': 'Sacoches & Housses PC',
    'Laptop Batteries': 'Batteries PC Portable',
    'Laptop LCD Screen': 'Écrans PC Portable',
    'Laptop Stands': 'Supports PC Portable',
    # Computer > Networking
    'Modem-Router Combos': 'Modems-Routeurs',
    'Networking Tools': 'Outils Réseau',
    # Computer > Office Electronics
    'PDAs': 'PDA',
    'Printers': 'Imprimantes',
    # Computer > Tablets
    'Tablet Accessories': 'Accessoires Tablettes',
    'Tablet LCDs & Panels': 'Écrans Tablettes',
    'Tablet Parts': 'Pièces Tablettes',
    'Tablets': 'Tablettes',
    # Consumer Electronics > Accessories & Parts
    'Batteries': 'Batteries',
    'Home Electronic Accessories': 'Accessoires Électroniques',
    # Consumer Electronics > Camera & Photo
    'Action Cameras': 'Caméras d\'Action',
    'Camera & Photo Accessories': 'Accessoires Photo',
    'Camera Drones': 'Drones Caméra',
    'Digital Cameras': 'Appareils Photo Numériques',
    # Consumer Electronics > Home Audio & Video
    'Audio Amplifiers': 'Amplificateurs Audio',
    'Home Audio & Video': 'Audio & Vidéo',
    # Consumer Electronics > Portable Audio & Video
    'Earphones & Headphones': 'Écouteurs & Casques',
    'Speakers': 'Enceintes',
    # Consumer Electronics > Smart Electronics
    'Smart Home Appliances': 'Maison Connectée',
    'Smart Wristbands': 'Bracelets Connectés',
    'Wearable Devices': 'Objets Connectés',
    # Home, Garden & Furniture > Bathroom
    'Bath Towels': 'Serviettes de Bain',
    'Bathroom Accessories': 'Accessoires Salle de Bain',
    'Bathroom Shelves': 'Étagères Salle de Bain',
    'Shower Curtains': 'Rideaux de Douche',
    'Toilet Seat Covers': 'Abattants WC',
    # Home > Festive
    'Christmas': 'Noël',
    'Event & Party': 'Événements & Fêtes',
    'Gift Bags & Wrapping Supplies': 'Emballages Cadeaux',
    # Home > Garden
    'Garden Tools': 'Outils de Jardin',
    'Pots & Planters': 'Pots & Jardinières',
    'Watering & Irrigation': 'Arrosage & Irrigation',
    # Home > Decor
    'Candles & Holders': 'Bougies & Bougeoirs',
    'Clocks': 'Horloges',
    'Decorative Films': 'Films Décoratifs',
    'Figurines & Miniatures': 'Figurines & Miniatures',
    'Flower Pots & Planters': 'Pots de Fleurs',
    'Frames': 'Cadres',
    'Painting & Calligraphy': 'Peinture & Calligraphie',
    'Stickers': 'Stickers Muraux',
    'Vases': 'Vases',
    'Wall Stickers': 'Stickers Muraux',
    # Home > Storage
    'Adult Wellness': 'Bien-Être Adulte',
    'Furniture': 'Mobilier',
    'Home Office Storage': 'Rangement Bureau',
    'Hooks & Rails': 'Crochets & Barres',
    'Storage Bags': 'Sacs de Rangement',
    'Storage Baskets': 'Paniers de Rangement',
    'Storage Boxes & Bins': 'Boîtes de Rangement',
    'Storage Holders & Racks': 'Étagères & Porte-Objets',
    # Home > Textile
    'Bedding': 'Literie',
    'Carpets & Rugs': 'Tapis & Moquettes',
    'Curtains': 'Rideaux',
    'Cushion Cover': 'Housses de Coussin',
    'Pillow': 'Oreillers',
    'Table Cloth': 'Nappes',
    # Home > Kitchen
    'Bar Accessories': 'Accessoires Bar',
    'Cooking Tools': 'Ustensiles de Cuisine',
    'Dinnerware': 'Vaisselle',
    'Drinkware': 'Verres & Tasses',
    'Kitchen Knives & Accessories': 'Couteaux & Accessoires',
    # Health > Bath & Body
    'Bath Brushes, Sponges & Scrubbers': 'Brosses & Éponges de Bain',
    'Soap': 'Savons',
    # Health > Hair Care
    'Braiders': 'Accessoires Tressage',
    'Combs': 'Peignes',
    'Curling Irons': 'Fers à Boucler',
    'Hair Clips': 'Pinces à Cheveux',
    'Hair Extensions & Wigs': 'Extensions & Perruques',
    'Hair Straightener': 'Lisseurs',
    'Styling Accessories': 'Accessoires Coiffure',
    # Health > Health Care
    'Health Monitors': 'Moniteurs de Santé',
    'Massage & Relaxation': 'Massage & Relaxation',
    # Health > Makeup
    'Beauty Essentials': 'Essentiels Beauté',
    'Brush': 'Pinceaux',
    'Eye Shadow': 'Fards à Paupières',
    'Eyebrow Enhancers': 'Sourcils',
    'Eyelashes': 'Faux Cils',
    'Face': 'Visage',
    'Lip': 'Lèvres',
    'Makeup Sets': 'Coffrets Maquillage',
    'Makeup Tools': 'Outils Maquillage',
    # Health > Nail Art
    'Nail Art Equipment': 'Équipement Ongles',
    'Nail Art Templates': 'Modèles Nail Art',
    'Nail Gel': 'Gel Ongles',
    'Nail Glitter': 'Paillettes Ongles',
    'Nail Polish': 'Vernis à Ongles',
    'Rhinestones & Decorations': 'Strass & Décorations',
    'Stickers & Decals': 'Stickers Ongles',
    # Health > Oral
    'Teeth Whitening': 'Blanchiment Dentaire',
    'Toothbrushes': 'Brosses à Dents',
    # Health > Shaving
    'Electric Shavers': 'Rasoirs Électriques',
    'Nose & Ear Trimmer': 'Tondeuses Nez & Oreilles',
    # Health > Skin Care
    'Cleansers': 'Nettoyants',
    'Cream': 'Crèmes',
    'Essential Oil': 'Huiles Essentielles',
    'Face Mask': 'Masques Visage',
    'Serum': 'Sérums',
    'Sunscreen': 'Protection Solaire',
    'Toner': 'Toniques',
    # Health > Skin Care Tools
    'Face Skin Care Tools': 'Outils Soins Visage',
    # Women's Clothing > Accessories
    'Belts & Cummerbunds': 'Ceintures',
    'Eyewear & Accessories': 'Lunettes & Accessoires',
    'Scarves & Wraps': 'Écharpes & Foulards',
    'Woman Gloves & Mittens': 'Gants Femme',
    'Woman Hats & Caps': 'Chapeaux Femme',
    'Woman Prescription Glasses': 'Lunettes de Vue Femme',
    'Woman Socks': 'Chaussettes Femme',
    # Women's Clothing > Bottoms
    'Leggings': 'Leggings',
    'Pants & Capris': 'Pantalons & Corsaires',
    'Skirts': 'Jupes',
    'Wide Leg Pants': 'Pantalons Larges',
    'Woman Jeans': 'Jeans Femme',
    'Woman Shorts': 'Shorts Femme',
    # Women's Clothing > Outerwear
    'Basic Jacket': 'Vestes Basiques',
    'Blazers': 'Blazers',
    'Leather & Suede': 'Cuir & Daim',
    'Woman Trench': 'Trenchs Femme',
    "Women's Padded Jackets": 'Doudounes Femme',
    'Wool & Blend': 'Laine & Mélanges',
    # Women's Clothing > Tops & Sets
    'Blouses & Shirts': 'Blouses & Chemisiers',
    'Jumpsuits': 'Combinaisons',
    'Ladies Short Sleeve': 'Manches Courtes Femme',
    'Lady Dresses': 'Robes',
    'Rompers': 'Barboteuses & Combishorts',
    'Suits & Sets': 'Ensembles & Tailleurs',
    'Sweaters': 'Pulls Femme',
    'Woman Hoodies & Sweatshirts': 'Sweats Femme',
    "Women's Camis": 'Débardeurs Femme',
    "Women's Long-Sleeved Shirts": 'Manches Longues Femme',
    "Women's Short-Sleeved Shirts": 'Manches Courtes Femme',
    "Women's Vests": 'Gilets Femme',
    # Men's Clothing > Accessories
    'Belts': 'Ceintures Homme',
    'Man Gloves & Mittens': 'Gants Homme',
    'Man Prescription Glasses': 'Lunettes de Vue Homme',
    "Men's Ties": 'Cravates',
    'Scarves': 'Écharpes Homme',
    'Socks': 'Chaussettes Homme',
    # Men's Clothing > Bottoms
    'Cargo Pants': 'Pantalons Cargo',
    'Casual Pants': 'Pantalons Décontractés',
    'Harem Pants': 'Pantalons Sarouel',
    'Man Jeans': 'Jeans Homme',
    'Man Shorts': 'Shorts Homme',
    'Pajama Sets': 'Pyjamas',
    'Sweatpants': 'Joggings',
    # Men's Clothing > Hats & Caps
    'Baseball Caps': 'Casquettes',
    'Berets': 'Bérets',
    'Fedoras': 'Fedoras',
    # Men's Clothing > Outerwear
    'Down Jackets': 'Doudounes Homme',
    'Man Hoodies & Sweatshirts': 'Sweats Homme',
    'Man Trench': 'Trenchs Homme',
    "Men's Jackets": 'Vestes Homme',
    "Men's Shirts": 'Chemises Homme',
    "Men's Suits": 'Costumes Homme',
    "Men's Sweaters": 'Pulls Homme',
    'Parkas': 'Parkas',
    'Suits & Blazer': 'Costumes & Blazers',
    'Wool & Blends': 'Laine & Mélanges Homme',
    # Men's Clothing > T-Shirts
    '3D': 'T-Shirts 3D',
    "Men's Long-Sleeved": 'Manches Longues Homme',
    'Print': 'T-Shirts Imprimés',
    'Solid': 'T-Shirts Unis',
    # Men's Clothing > Underwear
    'Boxers': 'Boxers',
    'Briefs': 'Slips',
    'Shorts': 'Shorts Homme',
    # Jewelry > Fashion Jewelry
    'Body Jewelry': 'Bijoux de Corps',
    'Bracelets & Bangles': 'Bracelets',
    'Brooches': 'Broches',
    'Charms': 'Charms & Breloques',
    'Earrings': 'Boucles d\'Oreilles',
    'Fashion Jewelry Sets': 'Parures Fantaisie',
    'Keychains': 'Porte-Clés',
    'Necklace & Pendants': 'Colliers & Pendentifs',
    'Rings': 'Bagues',
    # Jewelry > Fine Jewelry
    'Fine Earrings': 'Boucles d\'Oreilles Fines',
    'K-Gold': 'Or',
    'Pearls Jewelry': 'Bijoux en Perles',
    # Jewelry > Watches
    'Digital Watches': 'Montres Digitales',
    'Quartz Watches': 'Montres à Quartz',
    "Children's Watches": 'Montres Enfant',
    'Dress Watches': 'Montres Habillées',
    'Women Sports Watches': 'Montres Sport Femme',
    # Jewelry > Wedding
    'Bridal Jewelry Sets': 'Parures de Mariée',
    # Bags & Shoes
    'Backpacks': 'Sacs à Dos',
    'Crossbody Bags': 'Sacs Bandoulière',
    'Shoulder Bags': 'Sacs à Main',
    'Wallets': 'Portefeuilles',
    'Waist Packs': 'Bananes',
    'Casual Shoes': 'Chaussures Décontractées',
    'Flats': 'Ballerines',
    'Heels': 'Talons',
    'Loafers': 'Mocassins',
    'Oxfords': 'Derbies',
    'Sandals': 'Sandales',
    'Slippers': 'Chaussons',
    'Vulcanize Shoes': 'Baskets',
    "Men's Boots": 'Bottes Homme',
    "Men's Casual Shoes": 'Chaussures Décontractées Homme',
    "Men's Sandals": 'Sandales Homme',
    "Men's Slippers": 'Pantoufles Homme',
    "Men's Vulcanize Shoes": 'Baskets Homme',
    'Luggage': 'Bagages',
    'Travel Accessories': 'Accessoires Voyage',
    'Travel Bags': 'Sacs de Voyage',
    "Men's Backpacks": 'Sacs à Dos Homme',
    "Men's Crossbody Bags": 'Sacs Bandoulière Homme',
    # Auto
    'Audio & Video': 'Audio & Vidéo Auto',
    'Car Alarms': 'Alarmes Auto',
    'Car Electronics Accessories': 'Accessoires Électroniques Auto',
    'Car Lights': 'Éclairage Auto',
    'DVR & Dash Camera': 'Dashcams',
    'GPS & Accessories': 'GPS & Accessoires',
    'Auto Bumpers': 'Pare-Chocs',
    'Auto Filters': 'Filtres Auto',
    'Exterior Door Items': 'Accessoires Portes',
    'Grilles': 'Calandres',
    'Mirrors': 'Rétroviseurs',
    'Exterior Accessories': 'Accessoires Extérieurs Auto',
    'Car Covers': 'Housses Auto',
    'Car Stickers': 'Autocollants Auto',
    'Car Wash & Maintenance': 'Lavage & Entretien',
    'Interior Accessories': 'Accessoires Intérieurs Auto',
    'Air Freshener': 'Désodorisants',
    'Car Organizers': 'Organiseurs Auto',
    'Car Seat Covers': 'Housses de Siège',
    'Ornaments': 'Ornements Auto',
    'Steering Covers': 'Couvre-Volants',
    'Sun Visors': 'Pare-Soleil',
    'Motorcycle Accessories & Parts': 'Accessoires Moto',
    'Motorcycle Equipments': 'Équipement Moto',
    'Motorcycle Lighting': 'Éclairage Moto',
    # Sports
    'Bicycle Frames': 'Cadres Vélo',
    'Bicycles': 'Vélos',
    'Cycling Eyewear': 'Lunettes Cyclisme',
    'Cycling Gloves': 'Gants Cyclisme',
    'Fishing Lures': 'Leurres de Pêche',
    'Camping & Hiking': 'Camping & Randonnée',
    'Fitness & Bodybuilding': 'Fitness & Musculation',
    'Golf': 'Golf',
    'Sports Accessories': 'Accessoires de Sport',
    'Bikini Sets': 'Bikinis',
    'Cover-Ups': 'Paréos',
    'One-Piece Suits': 'Maillots Une Pièce',
    'Two-Piece Suits': 'Maillots Deux Pièces',
    # Home Improvement
    'Flashlights & Torches': 'Lampes Torches',
    'Hand Tools': 'Outils à Main',
    'Home Improvement Materials': 'Matériaux de Rénovation',
    'Power Tools': 'Outils Électriques',
    'Tool Sets': 'Coffrets d\'Outils',
    'Tools Storage': 'Rangement Outils',
    # Pet
    'Pet Clothings': 'Vêtements',
    'Pet Scarves': 'Écharpes',
    'Pet Shoes & Socks': 'Chaussures & Chaussettes',
    'Pet Sweatshirts & Hoodies': 'Sweats',
    'Pet Beds': 'Lits',
    'Pet Mats': 'Tapis',
    'Pet Nests': 'Nids & Coussins',
    'Pet Bows & Ties': 'Nœuds & Cravates',
    'Pet Collars': 'Colliers',
    'Pet Glasses': 'Lunettes',
    'Pet Harnesses': 'Harnais',
    'Pet Leashes': 'Laisses',
    'Pet Bowls': 'Gamelles',
    'Pet Drinking Tools': 'Abreuvoirs',
    'Pet Feeding Tools': 'Distributeurs',
    'Cat Trees & Condos': 'Arbres à Chat',
    'Pet Furniture Tools': 'Accessoires Mobilier',
    'Pet Houses & Cages': 'Maisons & Cages',
    'Pet Hair Removers & Combs': 'Brosses & Peignes',
    'Pet Shower Products': 'Produits de Toilette',
    'Pet Snacks': 'Friandises',
    'Pet Chase Toys': 'Jouets de Poursuite',
    'Pet Chew Toys': 'Jouets à Mâcher',
    'Pet Plush Toys': 'Peluches',
    'Pet Sound Toys': 'Jouets Sonores',
    'Pet Toy Set': 'Coffrets de Jouets',
    # Toys, Kids & Babies
    'Activity & Gear': 'Activité & Équipement',
    'Baby Care': 'Soins Bébé',
    'Backpacks & Carriers': 'Sacs & Porte-Bébés',
    'Baby Rompers': 'Grenouillères',
    'Boy Accessories': 'Accessoires Garçon',
    'Girl Accessories': 'Accessoires Fille',
    'Girl Clothing Sets': 'Ensembles Fille',
    'Girl Dresses': 'Robes Fille',
    'Tops & Tees': 'Hauts & T-Shirts',
    'Action & Toy Figures': 'Figurines & Jouets d\'Action',
    'Blocks': 'Blocs de Construction',
    'RC Helicopters': 'Hélicoptères Télécommandés',
    'Stuffed & Plush Animals': 'Peluches & Doudous',
}


def make_slug(name, parent_slug=None):
    """Créer un slug à partir d'un nom"""
    slug = name.lower()
    slug = slug.replace('&', 'et').replace("'", '').replace('"', '')
    slug = re.sub(r'[^a-z0-9àâäéèêëïîôùûüÿçœæ]+', '-', slug)
    slug = slug.strip('-')
    if parent_slug:
        slug = f"{parent_slug}-{slug}"
    return slug[:120]


with app.app_context():
    print("="*80)
    print("CRÉATION DE LA HIÉRARCHIE MPS 3 NIVEAUX")
    print("="*80)
    
    # Charger les catégories CJ
    cj_cats = Category.query.filter(Category.cj_category_id.isnot(None)).all()
    cj_by_id = {c.cj_category_id: c for c in cj_cats}
    
    # Compter produits par CJ category_id
    products = Product.query.filter(Product.cj_pid.isnot(None)).all()
    prod_by_cj = {}
    for p in products:
        if not p.cj_raw_data:
            continue
        try:
            raw = json.loads(p.cj_raw_data)
            cid = str(raw.get('categoryId') or raw.get('category_id') or '')
            if cid:
                prod_by_cj[cid] = prod_by_cj.get(cid, 0) + 1
        except:
            pass
    
    # Identifier les catégories CJ L2 et L3 utilisées
    used_l3_ids = set()
    used_l2_ids = set()
    
    for cj_id in prod_by_cj.keys():
        cat = cj_by_id.get(cj_id)
        if not cat:
            continue
        if cat.level == 3:
            used_l3_ids.add(cat.id)
            if cat.parent:
                used_l2_ids.add(cat.parent_id)
        elif cat.level == 2:
            used_l2_ids.add(cat.id)
    
    print(f"\nCatégories CJ L2 utilisées: {len(used_l2_ids)}")
    print(f"Catégories CJ L3 utilisées: {len(used_l3_ids)}")
    
    # Mapping CJ L1 -> MPS L1
    cj_l1s = [c for c in cj_cats if c.level == 1]
    
    # Créer les nouvelles catégories MPS L2 et L3
    created_l2 = 0
    created_l3 = 0
    
    # Mapping : cj_category_id -> nouveau MPS category id
    cj_to_mps = {}
    
    # Vérifier les slugs existants pour éviter les doublons
    existing_slugs = set(c.slug for c in Category.query.all())
    
    def unique_slug(base_slug):
        slug = base_slug
        i = 2
        while slug in existing_slugs:
            slug = f"{base_slug}-{i}"
            i += 1
        existing_slugs.add(slug)
        return slug
    
    for l1 in sorted(cj_l1s, key=lambda x: x.name):
        mps_l1_id = CJ_L1_TO_MPS.get(l1.name)
        if not mps_l1_id:
            continue
        
        mps_l1 = db.session.get(Category, mps_l1_id)
        if not mps_l1:
            continue
        
        # Catégories CJ L2 sous ce L1
        l2s = [c for c in cj_cats if c.parent_id == l1.id and c.id in used_l2_ids]
        
        for l2 in sorted(l2s, key=lambda x: x.name):
            # Déterminer le MPS L1 cible (avec overrides)
            target_mps_l1_id = CJ_L2_MPS_OVERRIDE.get(l2.name, mps_l1_id)
            target_mps_l1 = db.session.get(Category, target_mps_l1_id)
            
            # Traduction FR du L2
            # Pour les catégories dupliquées (Accessories, Bottoms, etc.), 
            # on utilise le contexte CJ L1 pour distinguer
            l2_key = l2.name
            if l2.name == 'Accessories' and l1.name == "Men's Clothing":
                l2_key = 'Accessories'
                l2_fr = 'Accessoires Homme'
            elif l2.name == 'Bottoms' and l1.name == "Men's Clothing":
                l2_fr = 'Bas Homme'
            elif l2.name == 'Outerwear & Jackets' and l1.name == "Men's Clothing":
                l2_fr = 'Vestes & Manteaux Homme'
            else:
                l2_fr = L2_TRANSLATIONS.get(l2.name, l2.name)
            
            # Créer la catégorie MPS L2
            l2_slug = unique_slug(make_slug(l2_fr, target_mps_l1.slug))
            
            new_l2 = Category(
                name=l2_fr,
                slug=l2_slug,
                parent_id=target_mps_l1_id,
                level=2,
                cj_category_id=None,  # Pas de lien CJ direct (c'est une catégorie MPS)
                name_fr=l2_fr,
                visible=True,
                is_active=True,
                order=created_l2,
            )
            db.session.add(new_l2)
            db.session.flush()  # Pour obtenir l'ID
            
            # Mapper le CJ L2 vers ce nouveau MPS L2
            cj_to_mps[l2.cj_category_id] = new_l2.id
            
            created_l2 += 1
            print(f"  L2: {target_mps_l1.name} > {l2_fr} (CJ: {l1.name} > {l2.name})")
            
            # Catégories CJ L3 sous ce L2
            l3s = [c for c in cj_cats if c.parent_id == l2.id and c.id in used_l3_ids]
            
            for l3 in sorted(l3s, key=lambda x: x.name):
                # Override L3
                l3_target_mps_l1_id = CJ_L3_MPS_OVERRIDE.get(l3.name)
                if l3_target_mps_l1_id and l3_target_mps_l1_id != target_mps_l1_id:
                    # Cette L3 va dans un autre MPS L1 -> on la met sous un L2 spécial
                    # Pour simplifier, on la met directement sous le MPS L1 cible comme L2
                    l3_fr = L3_TRANSLATIONS.get(l3.name, l3.name)
                    l3_target = db.session.get(Category, l3_target_mps_l1_id)
                    l3_slug = unique_slug(make_slug(l3_fr, l3_target.slug))
                    
                    new_l3 = Category(
                        name=l3_fr,
                        slug=l3_slug,
                        parent_id=l3_target_mps_l1_id,
                        level=2,  # Comme L2 sous le MPS L1 cible
                        name_fr=l3_fr,
                        visible=True,
                        is_active=True,
                        order=created_l3,
                    )
                    db.session.add(new_l3)
                    db.session.flush()
                    cj_to_mps[l3.cj_category_id] = new_l3.id
                    created_l3 += 1
                    print(f"    L3 (override): {l3_target.name} > {l3_fr} (CJ: {l3.name})")
                else:
                    l3_fr = L3_TRANSLATIONS.get(l3.name, l3.name)
                    l3_slug = unique_slug(make_slug(l3_fr, new_l2.slug))
                    
                    new_l3 = Category(
                        name=l3_fr,
                        slug=l3_slug,
                        parent_id=new_l2.id,
                        level=3,
                        name_fr=l3_fr,
                        visible=True,
                        is_active=True,
                        order=created_l3,
                    )
                    db.session.add(new_l3)
                    db.session.flush()
                    cj_to_mps[l3.cj_category_id] = new_l3.id
                    created_l3 += 1
                    print(f"    L3: {l2_fr} > {l3_fr} (CJ: {l3.name})")
    
    db.session.commit()
    
    print(f"\n{'='*80}")
    print(f"Créées: {created_l2} catégories L2, {created_l3} catégories L3")
    print(f"{'='*80}")
    
    # ============================================================
    # REMAPPER LES PRODUITS
    # ============================================================
    print(f"\nREMAPPAGE DES PRODUITS...")
    
    remapped = 0
    orphans = 0
    
    for p in products:
        if not p.cj_raw_data:
            orphans += 1
            continue
        try:
            raw = json.loads(p.cj_raw_data)
            cid = str(raw.get('categoryId') or raw.get('category_id') or '')
        except:
            orphans += 1
            continue
        
        if not cid:
            orphans += 1
            continue
        
        # Chercher le mapping CJ -> MPS
        new_mps_id = cj_to_mps.get(cid)
        
        if not new_mps_id:
            # Essayer de remonter au L2 ou L1
            cj_cat = cj_by_id.get(cid)
            if cj_cat:
                if cj_cat.parent and cj_cat.parent.cj_category_id in cj_to_mps:
                    new_mps_id = cj_to_mps[cj_cat.parent.cj_category_id]
                elif cj_cat.parent and cj_cat.parent.parent:
                    # Remonter au L1
                    l1 = cj_cat.parent.parent if cj_cat.level == 3 else cj_cat.parent
                    new_mps_id = CJ_L1_TO_MPS.get(l1.name)
            
            if not new_mps_id:
                orphans += 1
                continue
        
        if p.category_id != new_mps_id:
            p.category_id = new_mps_id
            remapped += 1
    
    db.session.commit()
    
    print(f"\nRemappés: {remapped}")
    print(f"Orphelins: {orphans}")
    
    # ============================================================
    # DISTRIBUTION FINALE
    # ============================================================
    print(f"\n{'='*80}")
    print("DISTRIBUTION FINALE (top 30)")
    print(f"{'='*80}\n")
    
    from sqlalchemy import func
    dist = Product.query.filter(Product.cj_pid.isnot(None)).with_entities(
        Product.category_id, func.count(Product.id)
    ).group_by(Product.category_id).all()
    
    for cat_id, count in sorted(dist, key=lambda x: x[1], reverse=True)[:30]:
        cat = db.session.get(Category, cat_id) if cat_id else None
        path = cat.full_path if cat else 'AUCUNE'
        print(f"  {count:>6} | {path}")
    
    print(f"\n  TOTAL: {sum(c for _,c in dist)} produits")
