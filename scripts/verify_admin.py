from app import create_app
from extensions import db
from models.user import User
from models.role import Role

def verify_admin():
    app = create_app()
    with app.app_context():
        print("=== VÉRIFICATION ADMIN ===")
        
        # Vérifier l'utilisateur admin
        admin = User.query.filter_by(email='admin@multiproshop.com').first()
        if admin:
            print(f"✅ Utilisateur admin trouvé:")
            print(f"   - Username: {admin.username}")
            print(f"   - Email: {admin.email}")
            print(f"   - Role ID: {admin.role_id}")
            if admin.role:
                print(f"   - Role name: {admin.role.name}")
                print(f"   - Est admin: {admin.role.name == 'admin'}")
            
            # Test du mot de passe
            password_ok = admin.check_password('admin123')
            print(f"   - Mot de passe 'admin123': {'✅ OK' if password_ok else '❌ ERREUR'}")
            
            # Test de la condition d'authentification admin
            role_check = getattr(admin.role, 'name', None) == 'admin'
            print(f"   - Condition admin route: {'✅ OK' if role_check else '❌ ERREUR'}")
            
        else:
            print("❌ Utilisateur admin non trouvé!")
        
        print(f"\n=== INFORMATIONS CONNEXION ===")
        print(f"URL de connexion admin: http://multiproshop.local/auth/admin-login")
        print(f"Identifiants:")
        print(f"  - Username: admin")
        print(f"  - Password: admin123")

if __name__ == '__main__':
    verify_admin()
