from app import app
from extensions import db
from models.category import Category
from slugify import slugify

# Données complètes des catégories (Niveau 1 > Niveau 2 > Niveau 3)
CATEGORIES_DATA = [
    {
        "name": "Électronique & High-Tech",
        "icon": "fa-tv",
        "children": [
            {"name": "TV & Home Cinéma", "items": ["Téléviseurs", "Projecteurs", "Barres de son", "Amplificateurs"]},
            {"name": "Audio & Sono", "items": ["Enceintes Bluetooth", "Casques audio", "Écouteurs", "Microphones"]},
            {"name": "Photo & Vidéo", "items": ["Appareils photo", "Caméras", "Drones", "Objectifs"]},
            {"name": "Consoles & Jeux", "items": ["PlayStation", "Xbox", "Nintendo", "PC Gaming"]}
        ]
    },
    {
        "name": "Informatique",
        "icon": "fa-laptop",
        "children": [
            {"name": "Ordinateurs", "items": ["PC portables", "PC bureau", "MacBook", "iMac"]},
            {"name": "Composants PC", "items": ["Processeurs", "Cartes graphiques", "RAM", "SSD"]},
            {"name": "Périphériques", "items": ["Claviers", "Souris", "Écrans", "Imprimantes"]}
        ]
    },
    {
        "name": "Téléphonie & Tablettes",
        "icon": "fa-mobile-alt",
        "children": [
            {"name": "Smartphones", "items": ["iPhone", "Samsung", "Xiaomi", "Huawei"]},
            {"name": "Tablettes", "items": ["iPad", "Android", "Windows"]},
            {"name": "Accessoires", "items": ["Coques", "Chargeurs", "Écouteurs"]}
        ]
    },
    {
        "name": "Mode & Vêtements",
        "icon": "fa-tshirt",
        "children": [
            {"name": "Homme", "items": ["T-shirts", "Chemises", "Pantalons", "Chaussures"]},
            {"name": "Femme", "items": ["Robes", "Tops", "Jupes", "Chaussures"]},
            {"name": "Enfant", "items": ["Bébé", "Fille", "Garçon"]}
        ]
    },
    {
        "name": "Maison & Jardin",
        "icon": "fa-home",
        "children": [
            {"name": "Meubles", "items": ["Canapés", "Tables", "Chaises", "Lits"]},
            {"name": "Décoration", "items": ["Tableaux", "Rideaux", "Tapis", "Luminaires"]},
            {"name": "Électroménager", "items": ["Réfrigérateurs", "Lave-linge", "Aspirateurs"]},
            {"name": "Jardin", "items": ["Tondeuses", "Barbecues", "Mobilier", "Plantes"]}
        ]
    },
    {
        "name": "Santé & Beauté",
        "icon": "fa-heartbeat",
        "children": [
            {"name": "Soins visage", "items": ["Crèmes", "Sérums", "Masques"]},
            {"name": "Maquillage", "items": ["Fond de teint", "Mascara", "Rouge à lèvres"]},
            {"name": "Parfums", "items": ["Femme", "Homme", "Mixte"]}
        ]
    },
    {
        "name": "Sports & Loisirs",
        "icon": "fa-futbol",
        "children": [
            {"name": "Fitness", "items": ["Tapis de course", "Vélos", "Haltères"]},
            {"name": "Sports équipe", "items": ["Football", "Basketball", "Tennis"]},
            {"name": "Outdoor", "items": ["Camping", "Randonnée", "Vélo"]}
        ]
    },
    {
        "name": "Bébés & Puériculture",
        "icon": "fa-baby",
        "children": [
            {"name": "Poussettes", "items": ["Combinées", "Cannes", "Doubles"]},
            {"name": "Chambre bébé", "items": ["Lits", "Commodes", "Déco"]},
            {"name": "Repas", "items": ["Biberons", "Chaises hautes", "Vaisselle"]}
        ]
    },
    {
        "name": "Jeux & Jouets",
        "icon": "fa-gamepad",
        "children": [
            {"name": "0-3 ans", "items": ["Éveil", "Peluches", "Hochets"]},
            {"name": "3-6 ans", "items": ["Poupées", "Voitures", "Déguisements"]},
            {"name": "6-12 ans", "items": ["LEGO", "Playmobil", "Jeux société"]}
        ]
    },
    {
        "name": "Auto & Moto",
        "icon": "fa-car",
        "children": [
            {"name": "Pièces auto", "items": ["Freins", "Batteries", "Filtres"]},
            {"name": "Accessoires", "items": ["GPS", "Caméras", "Housses"]},
            {"name": "Moto", "items": ["Casques", "Blousons", "Gants"]}
        ]
    },
    {
        "name": "Bricolage & Outillage",
        "icon": "fa-tools",
        "children": [
            {"name": "Électroportatif", "items": ["Perceuses", "Scies", "Ponceuses"]},
            {"name": "Outillage main", "items": ["Marteaux", "Tournevis", "Clés"]},
            {"name": "Quincaillerie", "items": ["Vis", "Chevilles", "Serrures"]}
        ]
    },
    {
        "name": "Alimentation & Boissons",
        "icon": "fa-shopping-basket",
        "children": [
            {"name": "Épicerie", "items": ["Pâtes", "Riz", "Conserves"]},
            {"name": "Boissons", "items": ["Eaux", "Jus", "Sodas"]},
            {"name": "Vins", "items": ["Rouges", "Blancs", "Rosés"]}
        ]
    },
    {
        "name": "Animalerie",
        "icon": "fa-paw",
        "children": [
            {"name": "Chiens", "items": ["Croquettes", "Jouets", "Accessoires"]},
            {"name": "Chats", "items": ["Croquettes", "Litières", "Arbres"]},
            {"name": "Aquarium", "items": ["Aquariums", "Filtres", "Poissons"]}
        ]
    },
    {
        "name": "Livres & Papeterie",
        "icon": "fa-book",
        "children": [
            {"name": "Livres", "items": ["Romans", "BD", "Mangas"]},
            {"name": "Fournitures", "items": ["Scolaire", "Bureau", "Beaux-arts"]}
        ]
    },
    {
        "name": "Culture & Divertissement",
        "icon": "fa-film",
        "children": [
            {"name": "Musique", "items": ["CD", "Vinyles", "Instruments"]},
            {"name": "Films", "items": ["DVD", "Blu-ray", "4K"]}
        ]
    },
    {
        "name": "Services & Cartes Cadeaux",
        "icon": "fa-gift",
        "children": [
            {"name": "Cartes cadeaux", "items": ["Magasins", "Restaurants", "Loisirs"]},
            {"name": "Abonnements", "items": ["Streaming", "Presse", "Logiciels"]}
        ]
    },
    {
        "name": "Immobilier & Véhicules",
        "icon": "fa-building",
        "children": [
            {"name": "Immobilier", "items": ["Vente", "Location", "Neuf"]},
            {"name": "Véhicules", "items": ["Voitures", "Motos", "Utilitaires"]}
        ]
    }
]

def import_categories():
    with app.app_context():
        print("\n" + "="*70)
        print("🚀 IMPORT MASSIF DES CATÉGORIES")
        print("="*70 + "\n")
        
        # Supprimer les catégories existantes
        Category.query.delete()
        db.session.commit()
        print("🗑️  Catégories existantes supprimées\n")
        
        order = 0
        total_main = 0
        total_sub = 0
        total_items = 0
        
        for main_data in CATEGORIES_DATA:
            order += 1
            # Créer catégorie principale (niveau 1)
            main_cat = Category(
                name=main_data["name"],
                slug=slugify(main_data["name"]),
                icon=main_data.get("icon", "fa-folder"),
                level=1,
                order=order
            )
            db.session.add(main_cat)
            db.session.flush()
            total_main += 1
            print(f"✅ {main_cat.name}")
            
            # Créer sous-catégories (niveau 2)
            for sub_data in main_data.get("children", []):
                sub_cat = Category(
                    name=sub_data["name"],
                    slug=slugify(f"{main_data['name']}-{sub_data['name']}"),
                    parent_id=main_cat.id,
                    level=2,
                    order=0
                )
                db.session.add(sub_cat)
                db.session.flush()
                total_sub += 1
                print(f"   ├─ {sub_cat.name}")
                
                # Créer items (niveau 3)
                for item_name in sub_data.get("items", []):
                    item_cat = Category(
                        name=item_name,
                        slug=slugify(f"{main_data['name']}-{sub_data['name']}-{item_name}"),
                        parent_id=sub_cat.id,
                        level=3,
                        order=0
                    )
                    db.session.add(item_cat)
                    total_items += 1
                
            print()
        
        db.session.commit()
        
        print("="*70)
        print(f"✅ IMPORT TERMINÉ !")
        print(f"   • Catégories principales: {total_main}")
        print(f"   • Sous-catégories: {total_sub}")
        print(f"   • Items: {total_items}")
        print(f"   • TOTAL: {total_main + total_sub + total_items} catégories")
        print("="*70 + "\n")

if __name__ == "__main__":
    import_categories()