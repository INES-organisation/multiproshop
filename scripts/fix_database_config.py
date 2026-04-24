from app import create_app
from extensions import db
from models.user import User
from models.role import Role

def fix_database_config():
    app = create_app()
    with app.app_context():
        print("=== DIAGNOSTIC BASE DE DONNÉES ===")
        print(f"Configuration DB: {app.config['SQLALCHEMY_DATABASE_URI']}")
        
        try:
            # Tester la connexion
            db.engine.execute(db.text('SELECT 1'))
            print("✅ Connexion à la base de données réussie")
            
            # Vérifier les utilisateurs
            users = User.query.all()
            print(f"Nombre d'utilisateurs: {len(users)}")
            
            admin = User.query.filter_by(email='admin@multiproshop.com').first()
            if admin:
                print(f"✅ Admin trouvé: {admin.username} (ID: {admin.id})")
                print(f"   Rôle: {admin.role.name if admin.role else 'Aucun'}")
            else:
                print("❌ Admin non trouvé - Recréation nécessaire")
                
                # Recréer l'admin
                print("Recréation de l'admin...")
                
                # Créer les rôles si nécessaire
                admin_role = Role.query.filter_by(name='admin').first()
                if not admin_role:
                    admin_role = Role(name='admin', description='Administrateur')
                    db.session.add(admin_role)
                    db.session.commit()
                
                # Créer l'admin
                admin = User(
                    username='admin',
                    email='admin@multiproshop.com',
                    role_id=admin_role.id
                )
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
                print("✅ Admin recréé avec succès")
                
        except Exception as e:
            print(f"❌ Erreur de connexion DB: {e}")
            print("Utilisation de SQLite par défaut...")
            
            # Forcer SQLite temporairement
            app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///multiproshop.db'
            
            # Recréer les tables
            db.drop_all()
            db.create_all()
            
            # Créer les rôles
            roles = [
                Role(name='client', description='Client'),
                Role(name='vendeur', description='Vendeur'),
                Role(name='admin', description='Administrateur'),
            ]
            db.session.add_all(roles)
            db.session.commit()
            
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
            
            print("✅ Base SQLite créée avec admin")

if __name__ == '__main__':
    fix_database_config()
