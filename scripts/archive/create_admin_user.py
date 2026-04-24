"""
Créer un utilisateur admin
"""
from app import app
from extensions import db
from models.user import User
from models.role import Role

with app.app_context():
    # Créer les rôles
    admin_role = Role.query.filter_by(name='admin').first()
    if not admin_role:
        admin_role = Role(name='admin')
        db.session.add(admin_role)
    
    user_role = Role.query.filter_by(name='user').first()
    if not user_role:
        user_role = Role(name='user')
        db.session.add(user_role)
    
    db.session.commit()
    
    # Créer l'utilisateur admin
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', email='admin@multiproshop.com')
        admin.set_password('admin123')
        admin.role = admin_role
        db.session.add(admin)
        db.session.commit()
        print("✅ Utilisateur admin créé")
        print("   Username: admin")
        print("   Password: admin123")
    else:
        print("ℹ️  Utilisateur admin existe déjà")
