"""Test de la route admin avec authentification"""
from app import create_app
from models.user import User
from models.role import Role
import traceback

app = create_app()

with app.app_context():
    try:
        print("Test de la route admin avec authentification...")
        
        # Récupérer l'utilisateur admin
        admin_user = User.query.join(Role).filter(Role.name == 'admin').first()
        
        if not admin_user:
            print("ERREUR: Aucun utilisateur admin trouvé")
        else:
            print(f"Utilisateur admin: {admin_user.username}")
            
            # Tester avec authentification
            with app.test_client() as client:
                # Se connecter
                with client.session_transaction() as sess:
                    sess['_user_id'] = str(admin_user.id)
                
                # Tester l'accès à la route
                print("Tentative d'accès à /admin/...")
                response = client.get('/admin/')
                print(f"Status code: {response.status_code}")
                
                if response.status_code == 500:
                    print("\n=== ERREUR 500 DÉTECTÉE ===")
                    print(response.data.decode('utf-8'))
                elif response.status_code == 200:
                    print("Succès! La page admin se charge correctement")
                else:
                    print(f"Code inattendu: {response.status_code}")
                    print(f"Location: {response.location if hasattr(response, 'location') else 'N/A'}")
            
    except Exception as e:
        print(f"\nERREUR PYTHON: {e}")
        print("\n=== TRACEBACK COMPLET ===")
        print(traceback.format_exc())
