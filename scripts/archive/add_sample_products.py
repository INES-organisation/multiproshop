"""
Script pour ajouter des produits de test dans la base de données
"""
from app import app
from extensions import db
from models.product import Product
from models.category import Category
from slugify import slugify
import random

# Données de produits par catégorie
PRODUCTS_DATA = {
    "Smartphones": [
        {"name": "iPhone 15 Pro Max", "brand": "Apple", "price": 1299.99, "compare_price": 1499.99, "stock": 15, "description": "Le smartphone le plus avancé d'Apple avec puce A17 Pro, caméra 48MP et écran Super Retina XDR de 6.7 pouces."},
        {"name": "Samsung Galaxy S24 Ultra", "brand": "Samsung", "price": 1199.99, "compare_price": 1399.99, "stock": 20, "description": "Smartphone premium avec S Pen intégré, zoom 100x et écran Dynamic AMOLED 2X de 6.8 pouces."},
        {"name": "Google Pixel 8 Pro", "brand": "Google", "price": 899.99, "stock": 12, "description": "Photographie exceptionnelle avec IA, processeur Google Tensor G3 et écran LTPO OLED de 6.7 pouces."},
        {"name": "Xiaomi 14 Pro", "brand": "Xiaomi", "price": 799.99, "compare_price": 899.99, "stock": 18, "description": "Smartphone haut de gamme avec Snapdragon 8 Gen 3, caméra Leica et charge rapide 120W."},
        {"name": "OnePlus 12", "brand": "OnePlus", "price": 699.99, "stock": 10, "description": "Performance exceptionnelle avec Snapdragon 8 Gen 3, écran 120Hz et charge ultra-rapide."},
    ],
    "Ordinateurs portables": [
        {"name": "MacBook Pro 14 M3", "brand": "Apple", "price": 1999.99, "stock": 8, "description": "Ordinateur portable professionnel avec puce M3, écran Liquid Retina XDR et autonomie exceptionnelle."},
        {"name": "Dell XPS 15", "brand": "Dell", "price": 1599.99, "compare_price": 1799.99, "stock": 12, "description": "PC portable premium avec écran OLED 4K, Intel Core i7 et design ultra-fin."},
        {"name": "Lenovo ThinkPad X1 Carbon", "brand": "Lenovo", "price": 1399.99, "stock": 15, "description": "Ultrabook professionnel léger avec clavier exceptionnel et sécurité renforcée."},
        {"name": "ASUS ROG Zephyrus G14", "brand": "ASUS", "price": 1299.99, "stock": 10, "description": "PC portable gaming compact avec AMD Ryzen 9 et NVIDIA RTX 4060."},
        {"name": "HP Spectre x360", "brand": "HP", "price": 1199.99, "stock": 9, "description": "Convertible 2-en-1 élégant avec écran tactile OLED et stylet inclus."},
    ],
    "Télévisions": [
        {"name": "Samsung QLED 65 pouces", "brand": "Samsung", "price": 1499.99, "compare_price": 1799.99, "stock": 5, "description": "TV QLED 4K avec Quantum HDR, 120Hz et Smart TV Tizen."},
        {"name": "LG OLED 55 pouces", "brand": "LG", "price": 1299.99, "stock": 7, "description": "TV OLED avec noirs parfaits, Dolby Vision IQ et webOS."},
        {"name": "Sony Bravia XR 65 pouces", "brand": "Sony", "price": 1699.99, "stock": 4, "description": "TV LED 4K avec processeur Cognitive XR et Google TV."},
        {"name": "TCL Mini LED 55 pouces", "brand": "TCL", "price": 799.99, "compare_price": 999.99, "stock": 12, "description": "TV Mini LED 4K avec QLED et Android TV à prix abordable."},
    ],
    "Casques audio": [
        {"name": "Sony WH-1000XM5", "brand": "Sony", "price": 349.99, "compare_price": 399.99, "stock": 25, "description": "Casque sans fil avec réduction de bruit active leader du marché et son Hi-Res."},
        {"name": "Apple AirPods Max", "brand": "Apple", "price": 549.99, "stock": 15, "description": "Casque premium avec audio spatial, réduction de bruit adaptative et design aluminium."},
        {"name": "Bose QuietComfort 45", "brand": "Bose", "price": 299.99, "stock": 20, "description": "Confort exceptionnel avec réduction de bruit Bose légendaire."},
        {"name": "Sennheiser Momentum 4", "brand": "Sennheiser", "price": 329.99, "stock": 18, "description": "Qualité audio audiophile avec 60h d'autonomie."},
    ],
    "Montres connectées": [
        {"name": "Apple Watch Series 9", "brand": "Apple", "price": 449.99, "stock": 30, "description": "Montre connectée avec puce S9, écran Always-On et suivi santé avancé."},
        {"name": "Samsung Galaxy Watch 6", "brand": "Samsung", "price": 349.99, "compare_price": 399.99, "stock": 25, "description": "Montre Wear OS avec suivi du sommeil, ECG et design élégant."},
        {"name": "Garmin Fenix 7", "brand": "Garmin", "price": 599.99, "stock": 12, "description": "Montre multisport avec GPS, cartographie et autonomie 18 jours."},
        {"name": "Fitbit Sense 2", "brand": "Fitbit", "price": 249.99, "stock": 20, "description": "Montre santé avec gestion du stress, ECG et suivi du sommeil."},
    ],
    "Tablettes": [
        {"name": "iPad Pro 12.9 M2", "brand": "Apple", "price": 1199.99, "stock": 10, "description": "Tablette professionnelle avec puce M2, écran Liquid Retina XDR et compatibilité Apple Pencil."},
        {"name": "Samsung Galaxy Tab S9", "brand": "Samsung", "price": 799.99, "compare_price": 899.99, "stock": 15, "description": "Tablette Android premium avec S Pen inclus et écran AMOLED 120Hz."},
        {"name": "iPad Air M1", "brand": "Apple", "price": 649.99, "stock": 18, "description": "Tablette polyvalente avec puce M1 et écran Liquid Retina 10.9 pouces."},
    ],
    "Appareils photo": [
        {"name": "Sony Alpha 7 IV", "brand": "Sony", "price": 2499.99, "stock": 6, "description": "Appareil photo hybride plein format 33MP avec autofocus IA et vidéo 4K 60fps."},
        {"name": "Canon EOS R6 Mark II", "brand": "Canon", "price": 2399.99, "stock": 5, "description": "Hybride 24MP avec stabilisation IBIS et rafale 40 fps."},
        {"name": "Nikon Z6 III", "brand": "Nikon", "price": 2199.99, "stock": 7, "description": "Appareil polyvalent avec capteur 24MP et vidéo 4K 120fps."},
    ],
    "Consoles de jeux": [
        {"name": "PlayStation 5", "brand": "Sony", "price": 499.99, "stock": 8, "description": "Console nouvelle génération avec SSD ultra-rapide et ray tracing."},
        {"name": "Xbox Series X", "brand": "Microsoft", "price": 499.99, "stock": 10, "description": "Console 4K avec 12 téraflops et Game Pass."},
        {"name": "Nintendo Switch OLED", "brand": "Nintendo", "price": 349.99, "stock": 20, "description": "Console hybride avec écran OLED 7 pouces."},
    ],
}

def add_sample_products():
    with app.app_context():
        print("\n" + "="*70)
        print("🎮 AJOUT DE PRODUITS DE TEST")
        print("="*70 + "\n")
        
        total_added = 0
        
        for category_name, products in PRODUCTS_DATA.items():
            # Trouver la catégorie
            category = Category.query.filter(Category.name.ilike(f'%{category_name}%')).first()
            
            if not category:
                print(f"⚠️  Catégorie '{category_name}' non trouvée, recherche alternative...")
                # Essayer de trouver une catégorie parent
                if "Smartphone" in category_name:
                    category = Category.query.filter(Category.name.ilike('%téléphone%')).first()
                elif "Ordinateur" in category_name:
                    category = Category.query.filter(Category.name.ilike('%informatique%')).first()
                elif "Télévision" in category_name or "TV" in category_name:
                    category = Category.query.filter(Category.name.ilike('%électronique%')).first()
                elif "Casque" in category_name or "audio" in category_name:
                    category = Category.query.filter(Category.name.ilike('%audio%')).first()
                elif "Montre" in category_name:
                    category = Category.query.filter(Category.name.ilike('%accessoire%')).first()
                elif "Tablette" in category_name:
                    category = Category.query.filter(Category.name.ilike('%tablette%')).first()
                elif "Appareil photo" in category_name:
                    category = Category.query.filter(Category.name.ilike('%photo%')).first()
                elif "Console" in category_name:
                    category = Category.query.filter(Category.name.ilike('%jeux%')).first()
                
                if not category:
                    # Utiliser la première catégorie disponible
                    category = Category.query.first()
                    print(f"   ℹ️  Utilisation de la catégorie par défaut: {category.name}")
            
            print(f"\n📦 {category_name} (Catégorie: {category.name})")
            
            for product_data in products:
                # Vérifier si le produit existe déjà
                existing = Product.query.filter_by(name=product_data['name']).first()
                if existing:
                    print(f"   ⏭️  {product_data['name']} (existe déjà)")
                    continue
                
                # Créer le produit
                product = Product(
                    name=product_data['name'],
                    slug=slugify(product_data['name']),
                    sku=f"SKU-{random.randint(10000, 99999)}",
                    brand=product_data.get('brand', ''),
                    price=product_data['price'],
                    compare_price=product_data.get('compare_price'),
                    stock=product_data['stock'],
                    description=product_data['description'],
                    short_description=product_data['description'][:100] + "...",
                    category_id=category.id,
                    weight=round(random.uniform(0.2, 2.5), 2),
                    is_active=True,
                    is_featured=random.choice([True, False]),
                    is_new=random.choice([True, False, False]),  # 33% de chance
                    low_stock_threshold=5
                )
                
                db.session.add(product)
                total_added += 1
                print(f"   ✅ {product_data['name']} - {product_data['price']}€ (Stock: {product_data['stock']})")
        
        db.session.commit()
        
        print("\n" + "="*70)
        print(f"✅ IMPORT TERMINÉ !")
        print(f"   • Produits ajoutés: {total_added}")
        print(f"   • Total produits en BD: {Product.query.count()}")
        print("="*70 + "\n")

if __name__ == "__main__":
    add_sample_products()
