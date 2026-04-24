from app import create_app, db
from sqlalchemy import text
from models import (
    Role, User, Category, Product, Order, OrderItem,
    Supplier, Marketplace, Video, AIRecommendation, ApiIntegration
)

def init_db():
    app = create_app()
    with app.app_context():
        print('Base utilisée :', app.config['SQLALCHEMY_DATABASE_URI'])
        
        # Utiliser une connexion pour exécuter les commandes SQL brutes
        with db.engine.connect() as connection:
            # Désactiver les contraintes de clé étrangère
            connection.execute(db.text('SET FOREIGN_KEY_CHECKS = 0;'))
            connection.commit()
            
            # Supprimer toutes les tables
            db.drop_all()
            
            # Recréer toutes les tables
            db.create_all()
            
            # Réactiver les contraintes de clé étrangère
            connection.execute(db.text('SET FOREIGN_KEY_CHECKS = 1;'))
            connection.commit()
        
        # Créer les rôles
        roles = [
            Role(name='client', description='Acheteur classique'),
            Role(name='vendeur', description='Marchand ou dropshipper'),
            Role(name='admin', description='Administrateur plateforme'),
        ]
        db.session.add_all(roles)
        db.session.commit()
        print('Rôles créés :', [r.name for r in roles])
        
        # Créer les catégories
        categories = [
            Category(name='Électronique', description='Produits électroniques et gadgets'),
            Category(name='Vêtements', description='Mode et accessoires'),
            Category(name='Livres', description='Livres et publications'),
            Category(name='Sports', description='Équipements et accessoires de sport'),
        ]
        db.session.add_all(categories)
        db.session.commit()
        
        # Créer les produits
        products = [
            Product(
                name='Smartphone XYZ',
                description='Un smartphone puissant avec un excellent appareil photo',
                price=699.99,
                stock=10,
                category_id=1,
                brand='TechBrand'
            ),
            Product(
                name='T-shirt Classic',
                description='T-shirt confortable en coton 100%',
                price=19.99,
                stock=50,
                category_id=2,
                brand='FashionBrand'
            ),
            Product(
                name='Python pour les Débutants',
                description='Apprenez Python facilement avec ce guide complet',
                price=29.99,
                stock=20,
                category_id=3,
                brand='TechBooks'
            ),
            Product(
                name='Ballon de Football',
                description='Ballon de football professionnel',
                price=49.99,
                stock=15,
                category_id=4,
                brand='SportPro'
            ),
            Product(
                name='Écouteurs Bluetooth',
                description='Écouteurs sans fil avec réduction de bruit active',
                price=149.99,
                stock=25,
                category_id=1,
                brand='AudioTech'
            ),
            Product(
                name='Jean Slim',
                description='Jean slim confortable et élégant',
                price=59.99,
                stock=30,
                category_id=2,
                brand='FashionBrand'
            ),
            Product(
                name='Flask Web Development',
                description='Guide complet sur le développement web avec Flask',
                price=39.99,
                stock=15,
                category_id=3,
                brand='TechBooks'
            ),
            Product(
                name='Tapis de Yoga',
                description='Tapis de yoga antidérapant et confortable',
                price=29.99,
                stock=40,
                category_id=4,
                brand='SportPro'
            ),
        ]
        db.session.add_all(products)
        
        # Créer un utilisateur de test
        test_user = User(
            username='test_user',
            email='test@example.com'
        )
        test_user.set_password('password123')
        db.session.add(test_user)
        
        db.session.commit()
        print("Base de données initialisée avec succès!")

if __name__ == '__main__':
    init_db()
