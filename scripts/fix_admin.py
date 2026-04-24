from app import create_app
from extensions import db
from models.user import User
from models.role import Role

def fix_admin():
    app = create_app()
    with app.app_context():
        print('=== RÉPARATION ADMIN ===')
        
        # Recréer toutes les tables
        print('Recréation des tables...')
        db.drop_all()
        db.create_all()
        print('Tables recréées avec succès!')
        
        # Créer les rôles
        print('Création des rôles...')
        roles_data = [
            ('client', 'Acheteur classique'),
            ('vendeur', 'Marchand ou dropshipper'),
            ('admin', 'Administrateur plateforme'),
        ]
        
        for role_name, description in roles_data:
            role = Role(name=role_name, description=description)
            db.session.add(role)
        
        db.session.commit()
        print(f'Rôles créés: {[r[0] for r in roles_data]}')
        
        # Récupérer le rôle admin
        admin_role = Role.query.filter_by(name='admin').first()
        if not admin_role:
            print('ERREUR: Rôle admin non trouvé!')
            return
        
        # Créer l'utilisateur admin
        print('Création de l\'utilisateur admin...')
        admin = User(
            username='admin',
            email='admin@multiproshop.com',
            role_id=admin_role.id
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        
        print('✅ Utilisateur admin créé avec succès!')
        print('   - Username: admin')
        print('   - Email: admin@multiproshop.com')
        print('   - Mot de passe: admin123')
        print('   - Rôle: admin')
        
        # Vérification
        print('\n=== VÉRIFICATION ===')
        admin_check = User.query.filter_by(email='admin@multiproshop.com').first()
        if admin_check and admin_check.role:
            print(f'✅ Admin vérifié: {admin_check.username} - Rôle: {admin_check.role.name}')
            password_ok = admin_check.check_password('admin123')
            print(f'✅ Mot de passe: {"OK" if password_ok else "ERREUR"}')
        else:
            print('❌ Erreur lors de la vérification!')

if __name__ == '__main__':
    fix_admin()
