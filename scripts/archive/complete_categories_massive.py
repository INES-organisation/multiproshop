"""
Import MASSIF de TOUTES les catégories possibles
Plus de 1000+ catégories sur 3 niveaux
"""
from app import app
from extensions import db
from models.category import Category
from slugify import slugify

# DONNÉES ULTRA-COMPLÈTES
MEGA_CATEGORIES = [
    {
        "name": "Électronique & High-Tech",
        "icon": "fa-tv",
        "children": [
            {
                "name": "TV & Home Cinéma",
                "items": ["Téléviseurs LED", "Téléviseurs OLED", "Téléviseurs QLED", "Téléviseurs 4K", 
                         "Téléviseurs 8K", "Projecteurs vidéo", "Écrans de projection", "Barres de son",
                         "Amplificateurs home cinéma", "Enceintes surround", "Lecteurs Blu-ray 4K",
                         "Lecteurs DVD", "Supports muraux TV", "Meubles TV", "Câbles HDMI",
                         "Télécommandes universelles", "Antennes TV", "Décodeurs TNT"]
            },
            {
                "name": "Audio & Sono",
                "items": ["Enceintes Bluetooth portables", "Enceintes WiFi", "Enceintes intelligentes",
                         "Casques audio filaires", "Casques sans fil", "Casques gaming", "Casques studio",
                         "Écouteurs intra-auriculaires", "Écouteurs True Wireless", "Microphones USB",
                         "Microphones XLR", "Microphones studio", "Tables de mixage", "Interfaces audio",
                         "Platines vinyle", "Amplis Hi-Fi", "Enceintes monitoring", "Câbles audio",
                         "Pieds de micro", "Mousses acoustiques"]
            },
            {
                "name": "Photo & Vidéo",
                "items": ["Appareils photo reflex", "Appareils photo hybrides", "Appareils photo compacts",
                         "Caméras vidéo 4K", "Caméscopes", "Caméras d'action", "Drones avec caméra",
                         "Drones FPV", "Objectifs grand angle", "Objectifs téléobjectifs", "Objectifs macro",
                         "Trépieds photo", "Trépieds vidéo", "Stabilisateurs gimbal", "Steadicam",
                         "Éclairages LED", "Flashs cobra", "Softbox", "Cartes mémoire SD",
                         "Cartes CF", "Sacs photo", "Filtres photo", "Batteries"]
            },
            {
                "name": "Consoles & Jeux Vidéo",
                "items": ["PlayStation 5", "PlayStation 4", "Xbox Series X/S", "Xbox One", "Nintendo Switch",
                         "Nintendo Switch OLED", "Steam Deck", "PC Gaming prémonté", "Jeux PS5", "Jeux Xbox",
                         "Jeux Switch", "Jeux PC", "Manettes PS5", "Manettes Xbox", "Joy-Con",
                         "Casques gaming", "Volants de course", "Joysticks", "Chaises gaming",
                         "Bureaux gaming", "Tapis de souris XXL", "Webcams streaming"]
            },
            {
                "name": "Domotique & Maison Connectée",
                "items": ["Amazon Echo", "Google Nest", "Apple HomePod", "Caméras de surveillance WiFi",
                         "Caméras extérieures", "Sonnettes vidéo", "Interphones vidéo", "Thermostats Nest",
                         "Thermostats intelligents", "Prises connectées", "Multiprises connectées",
                         "Ampoules Philips Hue", "Ampoules connectées", "Rubans LED", "Serrures connectées",
                         "Détecteurs de fumée", "Détecteurs de mouvement", "Capteurs de porte",
                         "Stations météo", "Hubs domotique", "Interrupteurs connectés"]
            },
            {
                "name": "Accessoires High-Tech",
                "items": ["Batteries externes", "Chargeurs sans fil", "Chargeurs rapides", "Câbles USB-C",
                         "Câbles Lightning", "Adaptateurs multiports", "Hubs USB", "Clés USB",
                         "Disques durs externes", "Supports téléphone", "Supports tablette",
                         "Protections écran", "Nettoyants écran", "Housses de protection"]
            }
        ]
    },
    {
        "name": "Informatique & Bureautique",
        "icon": "fa-laptop",
        "children": [
            {
                "name": "Ordinateurs Portables",
                "items": ["PC portables 13 pouces", "PC portables 15 pouces", "PC portables 17 pouces",
                         "Ultrabooks", "PC portables gaming", "MacBook Air", "MacBook Pro 14", "MacBook Pro 16",
                         "Chromebooks", "PC portables professionnels", "PC portables étudiants",
                         "Stations de travail mobiles", "PC convertibles 2-en-1"]
            },
            {
                "name": "Ordinateurs de Bureau",
                "items": ["PC de bureau complets", "PC gaming tour", "PC bureautique", "iMac 24", "iMac 27",
                         "Mac Studio", "Mac Mini", "PC tout-en-un", "Mini PC", "Barebone PC",
                         "Stations de travail", "Serveurs", "PC silencieux"]
            },
            {
                "name": "Composants PC",
                "items": ["Processeurs Intel Core", "Processeurs AMD Ryzen", "Cartes graphiques NVIDIA",
                         "Cartes graphiques AMD", "Cartes mères Intel", "Cartes mères AMD", "Mémoire RAM DDR4",
                         "Mémoire RAM DDR5", "SSD NVMe", "SSD SATA", "Disques durs 3.5", "Disques durs 2.5",
                         "Boîtiers PC ATX", "Boîtiers Mini-ITX", "Alimentations modulaires",
                         "Alimentations 80+ Gold", "Ventilateurs 120mm", "Ventilateurs 140mm",
                         "Watercooling AIO", "Watercooling custom", "Pâte thermique", "Câbles sleeved"]
            },
            {
                "name": "Périphériques",
                "items": ["Claviers mécaniques", "Claviers gaming RGB", "Claviers sans fil", "Claviers ergonomiques",
                         "Souris gaming", "Souris sans fil", "Souris ergonomiques", "Trackballs",
                         "Écrans 24 pouces", "Écrans 27 pouces", "Écrans 32 pouces", "Écrans 4K",
                         "Écrans gaming 144Hz", "Écrans gaming 240Hz", "Écrans incurvés", "Écrans ultrawide",
                         "Webcams HD", "Webcams 4K", "Imprimantes laser", "Imprimantes jet d'encre",
                         "Imprimantes multifonctions", "Scanners", "Tablettes graphiques Wacom"]
            },
            {
                "name": "Stockage & Réseaux",
                "items": ["Disques durs externes 1To", "Disques durs externes 2To", "Disques durs externes 4To",
                         "SSD externes", "Clés USB 32Go", "Clés USB 64Go", "Clés USB 128Go",
                         "NAS 2 baies", "NAS 4 baies", "Routeurs WiFi 6", "Routeurs gaming",
                         "Switches Gigabit", "Switches 10G", "CPL WiFi", "Répéteurs WiFi",
                         "Cartes réseau WiFi", "Cartes réseau Ethernet", "Câbles Ethernet Cat6"]
            },
            {
                "name": "Logiciels & Licences",
                "items": ["Windows 11 Home", "Windows 11 Pro", "Office 365", "Office 2021",
                         "Antivirus Norton", "Antivirus Kaspersky", "Adobe Photoshop", "Adobe Premiere Pro",
                         "Adobe Creative Cloud", "AutoCAD", "Logiciels de montage vidéo", "VPN NordVPN",
                         "VPN ExpressVPN", "Jeux PC Steam", "Jeux PC Epic", "Utilitaires système"]
            }
        ]
    },
    {
        "name": "Téléphonie & Tablettes",
        "icon": "fa-mobile-alt",
        "children": [
            {
                "name": "Smartphones Apple",
                "items": ["iPhone 15 Pro Max", "iPhone 15 Pro", "iPhone 15 Plus", "iPhone 15",
                         "iPhone 14", "iPhone 13", "iPhone SE", "iPhone reconditionnés"]
            },
            {
                "name": "Smartphones Samsung",
                "items": ["Samsung Galaxy S24 Ultra", "Samsung Galaxy S24+", "Samsung Galaxy S24",
                         "Samsung Galaxy Z Fold", "Samsung Galaxy Z Flip", "Samsung Galaxy A54",
                         "Samsung Galaxy A34", "Samsung Galaxy A14"]
            },
            {
                "name": "Smartphones Xiaomi",
                "items": ["Xiaomi 14 Pro", "Xiaomi 14", "Xiaomi 13T Pro", "Xiaomi Redmi Note 13",
                         "Xiaomi Redmi 12", "Poco X6 Pro", "Poco F5"]
            },
            {
                "name": "Autres Smartphones",
                "items": ["Google Pixel 8 Pro", "Google Pixel 8", "OnePlus 12", "OnePlus 11",
                         "OPPO Find X6", "Huawei P60", "Honor Magic 5", "Realme GT 5"]
            },
            {
                "name": "Tablettes Apple",
                "items": ["iPad Pro 12.9", "iPad Pro 11", "iPad Air", "iPad 10.9", "iPad mini"]
            },
            {
                "name": "Tablettes Android",
                "items": ["Samsung Galaxy Tab S9", "Samsung Galaxy Tab A9", "Xiaomi Pad 6",
                         "Lenovo Tab P12", "Huawei MatePad"]
            },
            {
                "name": "Liseuses",
                "items": ["Kindle Paperwhite", "Kindle Oasis", "Kobo Clara", "Kobo Libra"]
            },
            {
                "name": "Accessoires Mobile",
                "items": ["Coques iPhone", "Coques Samsung", "Coques transparentes", "Coques antichoc",
                         "Protections écran verre trempé", "Films hydrogel", "Chargeurs secteur",
                         "Chargeurs voiture", "Câbles USB-C", "Câbles Lightning", "Batteries externes 10000mAh",
                         "Batteries externes 20000mAh", "Supports voiture magnétiques", "Supports voiture grille",
                         "Écouteurs Lightning", "Écouteurs USB-C", "Selfie sticks", "Trépieds smartphone"]
            },
            {
                "name": "Montres Connectées",
                "items": ["Apple Watch Series 9", "Apple Watch SE", "Apple Watch Ultra 2",
                         "Samsung Galaxy Watch 6", "Samsung Galaxy Watch 6 Classic", "Fitbit Charge 6",
                         "Fitbit Versa 4", "Garmin Fenix 7", "Garmin Forerunner", "Amazfit GTR 4",
                         "Bracelets Apple Watch", "Bracelets Samsung", "Chargeurs montres"]
            }
        ]
    },
    {
        "name": "Mode & Vêtements",
        "icon": "fa-tshirt",
        "children": [
            {
                "name": "Vêtements Homme",
                "items": ["T-shirts unis", "T-shirts imprimés", "Polos", "Chemises casual",
                         "Chemises business", "Pulls col rond", "Pulls col V", "Sweats à capuche",
                         "Sweats zippés", "Gilets", "Pantalons chino", "Pantalons costume",
                         "Jeans slim", "Jeans regular", "Jeans bootcut", "Costumes 2 pièces",
                         "Costumes 3 pièces", "Vestes de costume", "Blazers", "Vestes en jean",
                         "Blousons cuir", "Parkas", "Doudounes", "Manteaux", "Shorts bermuda",
                         "Shorts sport", "Caleçons", "Boxers", "Chaussettes", "Maillots de bain"]
            },
            {
                "name": "Vêtements Femme",
                "items": ["Robes courtes", "Robes longues", "Robes de soirée", "Robes casual",
                         "Tops basiques", "Blouses", "Chemisiers", "Tuniques", "Débardeurs",
                         "Pantalons droits", "Pantalons slim", "Pantalons palazzo", "Jeans skinny",
                         "Jeans mom", "Jeans flare", "Jupes courtes", "Jupes midi", "Jupes longues",
                         "Pulls fins", "Pulls épais", "Gilets longs", "Cardigans", "Vestes blazer",
                         "Vestes en jean", "Vestes cuir", "Manteaux laine", "Trenchs", "Doudounes",
                         "Parkas", "Combinaisons", "Lingerie soutiens-gorge", "Lingerie culottes",
                         "Maillots de bain 1 pièce", "Maillots de bain 2 pièces", "Bikinis"]
            }
        ]
    }
]

def add_massive_categories():
    with app.app_context():
        print("\n" + "="*70)
        print("🚀 AJOUT MASSIF DE CATÉGORIES SUPPLÉMENTAIRES")
        print("="*70 + "\n")
        
        # Compter les catégories existantes
        existing_count = Category.query.count()
        print(f"📊 Catégories existantes: {existing_count}\n")
        
        added_main = 0
        added_sub = 0
        added_items = 0
        
        for main_data in MEGA_CATEGORIES:
            # Vérifier si la catégorie principale existe déjà
            main_cat = Category.query.filter_by(name=main_data["name"], level=1).first()
            
            if not main_cat:
                # Créer la catégorie principale
                max_order = db.session.query(db.func.max(Category.order)).filter_by(level=1).scalar() or 0
                main_cat = Category(
                    name=main_data["name"],
                    slug=slugify(main_data["name"]),
                    icon=main_data.get("icon", "fa-folder"),
                    level=1,
                    order=max_order + 1
                )
                db.session.add(main_cat)
                db.session.flush()
                added_main += 1
                print(f"✅ Nouvelle catégorie: {main_cat.name}")
            else:
                print(f"ℹ️  Existe déjà: {main_cat.name}")
            
            # Ajouter les sous-catégories
            for sub_data in main_data.get("children", []):
                sub_cat = Category.query.filter_by(
                    name=sub_data["name"],
                    parent_id=main_cat.id,
                    level=2
                ).first()
                
                if not sub_cat:
                    import time
                    slug_base = slugify(f"{main_data['name']}-{sub_data['name']}")
                    # Vérifier si le slug existe déjà
                    existing_slug = Category.query.filter_by(slug=slug_base).first()
                    if existing_slug:
                        slug_base = f"{slug_base}-{int(time.time())}"
                    
                    sub_cat = Category(
                        name=sub_data["name"],
                        slug=slug_base,
                        parent_id=main_cat.id,
                        level=2,
                        order=0
                    )
                    db.session.add(sub_cat)
                    db.session.flush()
                    added_sub += 1
                    print(f"   ├─ Nouvelle sous-catégorie: {sub_cat.name}")
                
                # Ajouter les items (niveau 3)
                for item_name in sub_data.get("items", []):
                    item_cat = Category.query.filter_by(
                        name=item_name,
                        parent_id=sub_cat.id,
                        level=3
                    ).first()
                    
                    if not item_cat:
                        import time
                        slug_base = slugify(f"{main_data['name']}-{sub_data['name']}-{item_name}")
                        # Vérifier si le slug existe déjà
                        existing_slug = Category.query.filter_by(slug=slug_base).first()
                        if existing_slug:
                            slug_base = f"{slug_base}-{int(time.time())}"
                        
                        item_cat = Category(
                            name=item_name,
                            slug=slug_base,
                            parent_id=sub_cat.id,
                            level=3,
                            order=0
                        )
                        db.session.add(item_cat)
                        added_items += 1
            
            print()
        
        db.session.commit()
        
        new_total = Category.query.count()
        
        print("="*70)
        print(f"✅ AJOUT TERMINÉ !")
        print(f"   • Nouvelles catégories principales: {added_main}")
        print(f"   • Nouvelles sous-catégories: {added_sub}")
        print(f"   • Nouveaux items: {added_items}")
        print(f"   • TOTAL AJOUTÉ: {added_main + added_sub + added_items}")
        print(f"   • TOTAL DANS LA BD: {new_total} catégories")
        print("="*70 + "\n")

if __name__ == "__main__":
    add_massive_categories()
