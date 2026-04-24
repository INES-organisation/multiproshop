import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from extensions import db
from models.user import User
from models.role import Role

# Forcer SQLite
os.environ['DATABASE_URL'] = 'sqlite:///multiproshop.db'

app = create_app()
with app.app_context():
    print("=== CRÉATION BASE SQLITE ===")
    print(f"Base utilisée: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    # Supprimer et recréer les tables
    db.drop_all()
    db.create_all()
    print("Tables créées")
    
    # Créer les rôles
    roles = [
        Role(name='client', description='Client'),
        Role(name='vendeur', description='Vendeur'),
        Role(name='admin', description='Administrateur'),
    ]
    db.session.add_all(roles)
    db.session.commit()
    print("Rôles créés")
    
    # Créer l'admin
    admin_role = Role.query.filter_by(name='admin').first()
    admin = User(
        username='admin',
        email='admin@multiproshop.com',
        role_id=admin_role.id
    )
    admin.set_password('admin123')
    db.session.add(admin)
    db.session.commit()
    
    print("✅ Admin créé avec SQLite!")
    print("Identifiants: admin@multiproshop.com / admin123")
