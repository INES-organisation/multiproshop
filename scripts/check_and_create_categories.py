"""
Script pour vérifier et créer des catégories de test
"""
import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from models.category import Category
from extensions import db

def check_and_create_categories():
    """Vérifie les catégories existantes et en crée si nécessaire"""
    
    with app.app_context():
        # Vérifier les catégories existantes
        categories = Category.query.all()
        print(f"\n📊 Nombre de catégories dans la base : {len(categories)}")
        
        if categories:
            print("\n✅ Catégories existantes :")
            for cat in categories:
                product_count = len(cat.products) if cat.products else 0
                print(f"  - {cat.name} (ID: {cat.id}, {product_count} produits)")
        else:
            print("\n⚠️  Aucune catégorie trouvée !")
            print("\n🔧 Création de catégories de test...")
            
            # Catégories de test
            test_categories = [
                {
                    'name': 'Électronique',
                    'description': 'TV, Audio, Vidéo et appareils électroniques'
                },
                {
                    'name': 'Informatique',
                    'description': 'Ordinateurs, tablettes et accessoires informatiques'
                },
                {
                    'name': 'Téléphones',
                    'description': 'Smartphones et accessoires mobiles'
                },
                {
                    'name': 'Mode & Vêtements',
                    'description': 'Vêtements pour homme, femme et enfant'
                },
                {
                    'name': 'Maison & Jardin',
                    'description': 'Décoration, meubles et articles de jardin'
                },
                {
                    'name': 'Sport & Fitness',
                    'description': 'Équipements sportifs et fitness'
                },
                {
                    'name': 'Beauté & Santé',
                    'description': 'Produits de beauté et de santé'
                },
                {
                    'name': 'Livres & Médias',
                    'description': 'Livres, musique, films et jeux vidéo'
                },
                {
                    'name': 'Jouets & Jeux',
                    'description': 'Jouets pour enfants et jeux de société'
                },
                {
                    'name': 'Auto & Moto',
                    'description': 'Pièces et accessoires automobiles'
                }
            ]
            
            created_count = 0
            for cat_data in test_categories:
                try:
                    # Vérifier si la catégorie existe déjà
                    existing = Category.query.filter_by(name=cat_data['name']).first()
                    if not existing:
                        category = Category(
                            name=cat_data['name'],
                            description=cat_data['description']
                        )
                        db.session.add(category)
                        created_count += 1
                        print(f"  ✓ Créée : {cat_data['name']}")
                    else:
                        print(f"  - Existe déjà : {cat_data['name']}")
                except Exception as e:
                    print(f"  ✗ Erreur pour {cat_data['name']}: {e}")
            
            if created_count > 0:
                try:
                    db.session.commit()
                    print(f"\n✅ {created_count} catégories créées avec succès !")
                except Exception as e:
                    db.session.rollback()
                    print(f"\n❌ Erreur lors de la sauvegarde : {e}")
            else:
                print("\n✓ Toutes les catégories existent déjà")
        
        # Vérifier à nouveau après création
        categories = Category.query.all()
        print(f"\n📊 Total final : {len(categories)} catégories")
        
        return len(categories)

if __name__ == '__main__':
    print("=" * 60)
    print("🔍 Vérification des catégories")
    print("=" * 60)
    
    count = check_and_create_categories()
    
    print("\n" + "=" * 60)
    if count > 0:
        print("✅ Catégories disponibles pour l'affichage")
    else:
        print("⚠️  Aucune catégorie disponible")
    print("=" * 60)
