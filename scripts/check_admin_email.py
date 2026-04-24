from app import create_app
from extensions import db
from models.user import User
from models.role import Role

def check_admin_email():
    app = create_app()
    with app.app_context():
        print("=== VÉRIFICATION IDENTIFIANTS ADMIN ===")
        
        # Vérifier avec l'email comme identifiant
        admin = User.query.filter_by(email='admin@multiproshop.com').first()
        if admin:
            print(f"✅ Utilisateur trouvé avec email:")
            print(f"   - Username: {admin.username}")
            print(f"   - Email: {admin.email}")
            print(f"   - Role: {admin.role.name if admin.role else 'Aucun'}")
            
            # Test du mot de passe
            password_test = admin.check_password('admin123')
            print(f"   - Test mot de passe 'admin123': {'✅ OK' if password_test else '❌ ERREUR'}")
            
            # Test de la condition de connexion (comme dans auth.py ligne 52)
            # user = User.query.filter((User.username == identifiant) | (User.email == identifiant)).first()
            test_query = User.query.filter((User.username == 'admin@multiproshop.com') | (User.email == 'admin@multiproshop.com')).first()
            print(f"   - Test requête connexion: {'✅ OK' if test_query else '❌ ERREUR'}")
            
        else:
            print("❌ Aucun utilisateur trouvé avec l'email admin@multiproshop.com")
        
        # Lister tous les utilisateurs
        print(f"\n=== TOUS LES UTILISATEURS ===")
        users = User.query.all()
        for user in users:
            role_name = user.role.name if user.role else "Aucun rôle"
            print(f"  - {user.username} ({user.email}) - Rôle: {role_name}")

if __name__ == '__main__':
    check_admin_email()
