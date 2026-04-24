"""
AJOUT ULTRA-MASSIF DE TOUTES LES CATÉGORIES RESTANTES
Inclut ABSOLUMENT TOUT ce qui peut être vendu
"""
from app import app
from extensions import db
from models.category import Category
from slugify import slugify
import time

# TOUTES LES CATÉGORIES RESTANTES - ULTRA COMPLET
ALL_REMAINING_CATEGORIES = [
    {
        "name": "Mode & Vêtements",
        "icon": "fa-tshirt",
        "children": [
            {
                "name": "Chaussures Homme",
                "items": ["Baskets running", "Baskets lifestyle", "Baskets montantes", "Chaussures de ville cuir",
                         "Richelieus", "Derbies", "Mocassins", "Loafers", "Boots Chelsea", "Boots désert",
                         "Boots motard", "Sandales cuir", "Tongs", "Espadrilles", "Chaussures de sport",
                         "Chaussures de trail", "Chaussures de football", "Chaussures de basketball",
                         "Chaussures de sécurité", "Bottes de travail", "Chaussons d'intérieur"]
            },
            {
                "name": "Chaussures Femme",
                "items": ["Baskets blanches", "Baskets colorées", "Baskets compensées", "Escarpins classiques",
                         "Escarpins à talons", "Escarpins ouverts", "Bottes hautes", "Bottes mi-mollet",
                         "Bottines à talons", "Bottines plates", "Bottines Chelsea", "Sandales plates",
                         "Sandales à talons", "Sandales compensées", "Nu-pieds", "Mules", "Ballerines",
                         "Mocassins femme", "Derbies femme", "Compensées espadrilles", "Chaussures de sport femme",
                         "Chaussons confort", "Pantoufles"]
            },
            {
                "name": "Chaussures Enfant",
                "items": ["Baskets bébé", "Baskets enfant", "Chaussures premiers pas", "Sandales enfant",
                         "Bottes de pluie", "Chaussures d'école", "Chaussures de sport enfant", "Chaussons bébé"]
            },
            {
                "name": "Sacs & Maroquinerie",
                "items": ["Sacs à main cuir", "Sacs à main toile", "Sacs bandoulière", "Sacs cabas",
                         "Sacs seau", "Pochettes soirée", "Sacs à dos femme", "Sacs à dos homme",
                         "Sacs à dos ordinateur", "Sacs de voyage", "Valises cabine", "Valises grande taille",
                         "Sacs de sport", "Portefeuilles homme", "Portefeuilles femme", "Porte-cartes",
                         "Porte-monnaie", "Ceintures cuir homme", "Ceintures cuir femme", "Ceintures tissu"]
            }
        ]
    },
    {
        "name": "Maison & Jardin",
        "icon": "fa-home",
        "children": [
            {
                "name": "Literie & Linge de maison",
                "items": ["Draps housses 90x190", "Draps housses 140x190", "Draps housses 160x200",
                         "Draps housses 180x200", "Draps plats", "Taies d'oreiller", "Housses de couette",
                         "Couettes 140x200", "Couettes 220x240", "Couettes 240x260", "Couettes été",
                         "Couettes hiver", "Couettes 4 saisons", "Oreillers mémoire de forme", "Oreillers plumes",
                         "Oreillers synthétiques", "Traversins", "Protège-matelas imperméables",
                         "Alèses", "Serviettes de bain", "Draps de bain", "Serviettes de toilette",
                         "Gants de toilette", "Peignoirs éponge", "Peignoirs polaire", "Nappes rectangulaires",
                         "Nappes rondes", "Sets de table", "Torchons de cuisine", "Maniques", "Tabliers"]
            },
            {
                "name": "Rangement & Organisation",
                "items": ["Boîtes de rangement plastique", "Boîtes de rangement tissu", "Paniers de rangement",
                         "Coffres de rangement", "Étagères murales", "Étagères modulables", "Cubes de rangement",
                         "Penderies", "Housses de rangement", "Cintres bois", "Cintres plastique",
                         "Cintres velours", "Organiseurs de tiroirs", "Séparateurs", "Boîtes à chaussures",
                         "Vide-poches", "Corbeilles", "Paniers à linge"]
            },
            {
                "name": "Petit électroménager",
                "items": ["Robots cuiseurs", "Robots pâtissiers", "Batteurs électriques", "Mixeurs plongeants",
                         "Blenders", "Centrifugeuses", "Extracteurs de jus", "Cafetières filtre",
                         "Cafetières expresso", "Machines à café automatiques", "Bouilloires électriques",
                         "Grille-pain 2 fentes", "Grille-pain 4 fentes", "Croque-monsieur", "Gaufriers",
                         "Crêpières", "Raclettes", "Fondues", "Friteuses", "Friteuses sans huile",
                         "Multicuiseurs", "Cuiseurs vapeur", "Cuiseurs riz", "Yaourtières", "Sorbetières",
                         "Machines à pain", "Hachoirs", "Trancheuses", "Presse-agrumes", "Moulins à café"]
            },
            {
                "name": "Jardin & Extérieur",
                "items": ["Tondeuses thermiques", "Tondeuses électriques", "Tondeuses robots", "Tondeuses manuelles",
                         "Taille-haies électriques", "Taille-haies thermiques", "Débroussailleuses", "Souffleurs",
                         "Scarificateurs", "Motoculteurs", "Tronçonneuses", "Broyeurs de végétaux",
                         "Barbecues charbon", "Barbecues gaz", "Barbecues électriques", "Planchas",
                         "Salons de jardin résine", "Salons de jardin bois", "Salons de jardin aluminium",
                         "Tables de jardin", "Chaises de jardin", "Fauteuils de jardin", "Transats",
                         "Bains de soleil", "Hamacs", "Parasols déportés", "Parasols droits", "Voiles d'ombrage",
                         "Piscines hors-sol", "Piscines gonflables", "Filtres piscine", "Robots piscine",
                         "Produits piscine", "Plantes extérieur", "Plantes intérieur", "Arbres", "Arbustes",
                         "Pots de fleurs", "Jardinières", "Terreau", "Engrais", "Arrosoirs", "Tuyaux d'arrosage",
                         "Arrosage automatique", "Outils de jardinage"]
            }
        ]
    },
    {
        "name": "Sports & Loisirs",
        "icon": "fa-futbol",
        "children": [
            {
                "name": "Cyclisme",
                "items": ["Vélos route", "Vélos VTT", "Vélos ville", "Vélos électriques", "VTT électriques",
                         "Vélos pliants", "Vélos enfant", "Draisiennes", "Casques vélo", "Gants vélo",
                         "Maillots cyclisme", "Cuissards", "Chaussures vélo route", "Chaussures VTT",
                         "Pédales automatiques", "Compteurs vélo", "GPS vélo", "Éclairages vélo",
                         "Antivols vélo", "Porte-vélos", "Sacoches vélo", "Pompes vélo", "Chambres à air",
                         "Pneus vélo", "Chaînes vélo", "Dérailleurs", "Freins vélo"]
            },
            {
                "name": "Running & Trail",
                "items": ["Chaussures running route", "Chaussures trail", "Chaussures running femme",
                         "Textiles running", "Shorts running", "Collants running", "Brassières sport",
                         "Montres GPS running", "Ceintures cardio", "Brassards smartphone", "Lampes frontales",
                         "Sacs d'hydratation", "Gourdes running", "Chaussettes running", "Casquettes running"]
            },
            {
                "name": "Musculation & Fitness",
                "items": ["Tapis de course pliants", "Tapis de course professionnels", "Vélos d'appartement",
                         "Vélos spinning", "Vélos elliptiques", "Rameurs", "Steppers", "Bancs de musculation",
                         "Cages à squat", "Barres olympiques", "Disques fonte", "Disques bumper",
                         "Haltères réglables", "Haltères fixes", "Kettlebells", "Élastiques de résistance",
                         "Sangles TRX", "Tapis de yoga", "Briques yoga", "Sangles yoga", "Ballons de gym",
                         "Rouleaux de massage", "Tapis de sol", "Gants musculation", "Sangles de tirage",
                         "Ceintures de force", "Protéines whey", "Gainers", "BCAA", "Créatine"]
            },
            {
                "name": "Sports collectifs",
                "items": ["Ballons de football", "Chaussures de foot", "Crampons", "Protège-tibias",
                         "Gants de gardien", "Ballons de basketball", "Chaussures de basket", "Paniers de basket",
                         "Ballons de volleyball", "Filets de volley", "Ballons de handball", "Ballons de rugby",
                         "Raquettes de tennis", "Balles de tennis", "Cordages tennis", "Chaussures de tennis",
                         "Raquettes de badminton", "Volants badminton", "Filets badminton",
                         "Tables de ping-pong", "Raquettes ping-pong", "Balles ping-pong"]
            },
            {
                "name": "Sports nautiques",
                "items": ["Maillots de bain natation", "Lunettes de natation", "Bonnets de bain", "Palmes",
                         "Tubas", "Masques de plongée", "Combinaisons néoprène", "Planches de surf",
                         "Planches de paddle", "Kayaks", "Canoës", "Gilets de sauvetage", "Bouées"]
            },
            {
                "name": "Camping & Randonnée",
                "items": ["Tentes 2 places", "Tentes 4 places", "Tentes familiales", "Sacs de couchage",
                         "Matelas gonflables", "Matelas autogonflants", "Réchauds camping", "Glacières",
                         "Lampes camping", "Lanternes", "Sacs à dos randonnée", "Bâtons de randonnée",
                         "Chaussures de randonnée", "Chaussures de trek", "Vestes imperméables",
                         "Polaires", "Doudounes", "Gourdes", "Popotes camping"]
            }
        ]
    },
    {
        "name": "Bricolage & Outillage",
        "icon": "fa-tools",
        "children": [
            {
                "name": "Matériaux de construction",
                "items": ["Ciment gris", "Ciment blanc", "Mortier", "Béton prêt à l'emploi", "Chaux",
                         "Plâtre", "Enduit de façade", "Enduit de lissage", "Sable à maçonner",
                         "Sable à enduire", "Gravier", "Gravillon", "Galets", "Scories", "Pouzzolane",
                         "Billes d'argile", "Parpaings", "Briques", "Briques réfractaires",
                         "Carreaux de plâtre", "Plaques de plâtre", "Rails placo", "Montants placo",
                         "Laine de verre", "Laine de roche", "Polystyrène", "Polyuréthane"]
            },
            {
                "name": "Ferraillage & Métaux",
                "items": ["Fers à béton 6mm", "Fers à béton 8mm", "Fers à béton 10mm", "Fers à béton 12mm",
                         "Treillis soudé", "Grillage à béton", "Fil de fer", "Fil d'attache",
                         "Tubes acier", "Tubes inox", "Tubes PVC", "Tubes cuivre", "Profilés acier",
                         "Cornières", "Fers plats", "Fers ronds", "Tôles acier", "Tôles alu",
                         "Tôles galvanisées", "Tôles perforées", "Grillages", "Barres de seuil"]
            },
            {
                "name": "Bois & Panneaux",
                "items": ["Planches sapin", "Planches chêne", "Planches pin", "Tasseaux", "Chevrons",
                         "Poutres", "Madriers", "Lambourdes", "Lames de terrasse", "Panneaux OSB",
                         "Panneaux contreplaqué", "Panneaux MDF", "Panneaux aggloméré", "Panneaux mélaminé",
                         "Parquets massifs", "Parquets contrecollés", "Parquets stratifiés",
                         "Lames PVC", "Plinthes", "Moulures", "Cimaises"]
            },
            {
                "name": "Quincaillerie générale",
                "items": ["Vis bois 3x20", "Vis bois 4x40", "Vis bois 5x50", "Vis agglo", "Vis inox",
                         "Vis tôle", "Vis placo", "Vis béton", "Clous", "Pointes", "Agrafes",
                         "Chevilles nylon", "Chevilles métalliques", "Chevilles à frapper", "Chevilles Molly",
                         "Écrous", "Boulons", "Rondelles", "Tire-fond", "Crochets", "Pitons",
                         "Équerres", "Cornières de renfort", "Pattes de fixation", "Colliers de serrage",
                         "Serre-câbles", "Chaînes", "Câbles acier", "Mousquetons", "Tendeurs"]
            },
            {
                "name": "Menuiserie & Serrurerie",
                "items": ["Charnières", "Paumelles", "Fiches", "Pivots", "Ferme-portes", "Butées de porte",
                         "Poignées de porte", "Béquilles", "Boutons de porte", "Serrures à encastrer",
                         "Serrures en applique", "Cylindres de serrure", "Verrous", "Targettes",
                         "Loquets", "Crémones", "Espagnolettes", "Gâches", "Rosaces", "Plaques de propreté"]
            },
            {
                "name": "Peinture & Décoration",
                "items": ["Peinture acrylique blanche", "Peinture glycéro", "Peinture satinée", "Peinture mate",
                         "Peinture brillante", "Sous-couche universelle", "Primaire d'accrochage",
                         "Peinture bois extérieur", "Peinture fer", "Peinture sol", "Lasure chêne",
                         "Lasure pin", "Lasure incolore", "Vernis bois", "Vernis parquet", "Cire",
                         "Pinceaux plats", "Pinceaux ronds", "Rouleaux laqueur", "Rouleaux anti-goutte",
                         "Bacs à peinture", "Grilles d'essorage", "Bâches de protection", "Rubans de masquage",
                         "Enduit de rebouchage", "Enduit de lissage", "Colle à papier peint", "Papiers peints"]
            },
            {
                "name": "Plomberie & Sanitaire",
                "items": ["Robinets lavabo", "Robinets évier", "Robinets douche", "Mitigeurs thermostatiques",
                         "Colonnes de douche", "Pommeaux de douche", "Flexibles de douche", "Éviers inox",
                         "Éviers résine", "Lavabos", "Vasques", "WC suspendus", "WC au sol",
                         "Réservoirs WC", "Mécanismes WC", "Abattants WC", "Baignoires acrylique",
                         "Baignoires fonte", "Receveurs de douche", "Parois de douche", "Portes de douche",
                         "Tuyaux PVC", "Tuyaux PER", "Tuyaux cuivre", "Raccords PVC", "Raccords laiton",
                         "Raccords rapides", "Siphons", "Joints", "Téflon", "Filasse", "Pâte à joint"]
            },
            {
                "name": "Électricité",
                "items": ["Interrupteurs va-et-vient", "Interrupteurs simple", "Prises 16A", "Prises USB",
                         "Prises étanches", "Disjoncteurs 10A", "Disjoncteurs 16A", "Disjoncteurs 20A",
                         "Disjoncteurs différentiels", "Tableaux électriques", "Peignes électriques",
                         "Câbles 1.5mm²", "Câbles 2.5mm²", "Gaines électriques", "Boîtes d'encastrement",
                         "Boîtes de dérivation", "Dominos", "Wagos", "Ampoules LED E27", "Ampoules LED E14",
                         "Ampoules LED GU10", "Tubes LED", "Spots encastrables", "Spots orientables",
                         "Réglettes LED", "Détecteurs de mouvement", "Minuteries", "Télérupteurs",
                         "Sonnettes", "Interphones", "Rallonges électriques", "Multiprises"]
            }
        ]
    },
    {
        "name": "Auto & Moto",
        "icon": "fa-car",
        "children": [
            {
                "name": "Entretien auto",
                "items": ["Huiles moteur 5W30", "Huiles moteur 5W40", "Huiles moteur 10W40", "Huiles diesel",
                         "Liquide de refroidissement", "Liquide de frein", "Liquide lave-glace",
                         "Liquide direction assistée", "Additifs moteur", "Additifs diesel", "Nettoyants moteur",
                         "Shampooings auto", "Cires de carrosserie", "Polish", "Rénovateurs plastiques",
                         "Nettoyants jantes", "Nettoyants intérieur", "Désodorisants", "Parfums auto"]
            },
            {
                "name": "Pièces détachées",
                "items": ["Plaquettes de frein avant", "Plaquettes de frein arrière", "Disques de frein",
                         "Tambours de frein", "Mâchoires de frein", "Amortisseurs avant", "Amortisseurs arrière",
                         "Ressorts de suspension", "Rotules de direction", "Biellettes", "Silent-blocs",
                         "Filtres à huile", "Filtres à air", "Filtres à carburant", "Filtres habitacle",
                         "Bougies d'allumage", "Bobines d'allumage", "Courroies de distribution",
                         "Courroies d'accessoires", "Galets tendeurs", "Batteries 60Ah", "Batteries 70Ah",
                         "Balais d'essuie-glace", "Phares avant", "Feux arrière", "Clignotants", "Rétroviseurs"]
            }
        ]
    },
    {
        "name": "Alimentation & Boissons",
        "icon": "fa-shopping-basket",
        "children": [
            {
                "name": "Produits frais",
                "items": ["Fruits frais", "Légumes frais", "Viandes fraîches", "Volailles", "Poissons",
                         "Fruits de mer", "Fromages", "Yaourts", "Laits", "Beurre", "Œufs", "Charcuterie"]
            },
            {
                "name": "Surgelés",
                "items": ["Légumes surgelés", "Fruits surgelés", "Poissons panés", "Pizzas surgelées",
                         "Plats cuisinés surgelés", "Glaces", "Sorbets", "Frites surgelées"]
            }
        ]
    }
]

def add_all_remaining():
    with app.app_context():
        print("\n" + "="*70)
        print("🚀 AJOUT ULTRA-MASSIF - TOUTES CATÉGORIES RESTANTES")
        print("="*70 + "\n")
        
        existing_count = Category.query.count()
        print(f"📊 Catégories existantes: {existing_count}\n")
        
        added_main = 0
        added_sub = 0
        added_items = 0
        
        for main_data in ALL_REMAINING_CATEGORIES:
            main_cat = Category.query.filter_by(name=main_data["name"], level=1).first()
            
            if not main_cat:
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
                print(f"✅ {main_cat.name}")
            else:
                print(f"ℹ️  {main_cat.name}")
            
            for sub_data in main_data.get("children", []):
                sub_cat = Category.query.filter_by(
                    name=sub_data["name"],
                    parent_id=main_cat.id,
                    level=2
                ).first()
                
                if not sub_cat:
                    slug_base = slugify(f"{main_data['name']}-{sub_data['name']}")
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
                    print(f"   ├─ {sub_cat.name}")
                
                for item_name in sub_data.get("items", []):
                    item_cat = Category.query.filter_by(
                        name=item_name,
                        parent_id=sub_cat.id,
                        level=3
                    ).first()
                    
                    if not item_cat:
                        slug_base = slugify(f"{main_data['name']}-{sub_data['name']}-{item_name}")
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
        print(f"   • Nouvelles principales: {added_main}")
        print(f"   • Nouvelles sous-catégories: {added_sub}")
        print(f"   • Nouveaux items: {added_items}")
        print(f"   • TOTAL AJOUTÉ: {added_main + added_sub + added_items}")
        print(f"   • TOTAL DANS LA BD: {new_total} catégories")
        print("="*70 + "\n")

if __name__ == "__main__":
    add_all_remaining()
