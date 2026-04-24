"""
Configuration pytest pour les tests
"""
import pytest
import os
import tempfile
from app import create_app
from extensions import db
from models.user import User
from models.role import Role
from models.product import Product
from models.category import Category

@pytest.fixture
def app():
    """Créer une instance de l'application pour les tests"""
    # Créer un fichier de base de données temporaire
    db_fd, db_path = tempfile.mkstemp()
    
    # Configuration de test
    test_config = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'SECRET_KEY': 'test-secret-key',
        'WTF_CSRF_ENABLED': False,  # Désactiver CSRF pour les tests
        'SERVER_NAME': 'localhost.localdomain'
    }
    
    # Créer l'application
    app = create_app()
    app.config.update(test_config)
    
    # Créer les tables
    with app.app_context():
        db.create_all()
        
        # Créer des données de test
        _create_test_data()
    
    yield app
    
    # Nettoyage
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """Client de test Flask"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Runner CLI de test"""
    return app.test_cli_runner()


@pytest.fixture
def auth_client(client, app):
    """Client authentifié en tant qu'admin"""
    with app.app_context():
        user = User.query.filter_by(username='admin').first()
        
    with client:
        client.post('/auth/login', data={
            'email': 'admin@test.com',
            'password': 'admin123'
        }, follow_redirects=True)
        yield client


def _create_test_data():
    """Créer des données de test dans la base"""
    # Créer les rôles
    admin_role = Role(id=1, name='admin')
    client_role = Role(id=2, name='client')
    db.session.add(admin_role)
    db.session.add(client_role)
    
    # Créer un utilisateur admin
    admin = User(
        username='admin',
        email='admin@test.com',
        role_id=1
    )
    admin.set_password('admin123')
    db.session.add(admin)
    
    # Créer un utilisateur client
    client = User(
        username='client',
        email='client@test.com',
        role_id=2
    )
    client.set_password('client123')
    db.session.add(client)
    
    # Créer des catégories
    cat1 = Category(
        name='Électronique',
        slug='electronique',
        level=1
    )
    cat2 = Category(
        name='Vêtements',
        slug='vetements',
        level=1
    )
    db.session.add(cat1)
    db.session.add(cat2)
    db.session.flush()  # Pour obtenir les IDs
    
    # Créer des produits
    product1 = Product(
        name='iPhone 13',
        description='Smartphone Apple',
        price=799.99,
        stock=10,
        category_id=cat1.id,
        is_active=True
    )
    product2 = Product(
        name='T-Shirt',
        description='T-shirt en coton',
        price=19.99,
        stock=50,
        category_id=cat2.id,
        is_active=True
    )
    product3 = Product(
        name='Produit inactif',
        description='Produit désactivé',
        price=9.99,
        stock=0,
        category_id=cat1.id,
        is_active=False
    )
    db.session.add(product1)
    db.session.add(product2)
    db.session.add(product3)
    
    db.session.commit()
