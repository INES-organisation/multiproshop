from app import create_app
from models.user import User

def test_login_flow():
    app = create_app()
    with app.app_context():
        print("=== TEST FLUX DE CONNEXION ADMIN ===")
        
        # Simuler exactement ce qui se passe dans auth.py ligne 50-54
        identifiant = 'admin@multiproshop.com'  # Ce que tu tapes
        password = 'admin123'  # Ce que tu tapes
        
        print(f"1. Identifiant saisi: {identifiant}")
        print(f"2. Mot de passe saisi: {password}")
        
        # Requête exacte de la ligne 52
        user = User.query.filter((User.username == identifiant) | (User.email == identifiant)).first()
        print(f"3. Utilisateur trouvé: {'Oui' if user else 'Non'}")
        
        if user:
            print(f"   - Username: {user.username}")
            print(f"   - Email: {user.email}")
            
            # Test du mot de passe (ligne 53)
            password_ok = user.check_password(password)
            print(f"4. Mot de passe correct: {'Oui' if password_ok else 'Non'}")
            
            if password_ok:
                # Test du rôle (ligne 54)
                role_name = getattr(user.role, 'name', None)
                print(f"5. Rôle de l'utilisateur: {role_name}")
                is_admin = role_name == 'admin'
                print(f"6. Est admin: {'Oui' if is_admin else 'Non'}")
                
                if is_admin:
                    print("✅ CONNEXION DEVRAIT RÉUSSIR!")
                else:
                    print("❌ Échec: Pas admin")
            else:
                print("❌ Échec: Mot de passe incorrect")
        else:
            print("❌ Échec: Utilisateur non trouvé")

if __name__ == '__main__':
    test_login_flow()
