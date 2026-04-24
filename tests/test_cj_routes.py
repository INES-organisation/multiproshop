"""Test des routes CJ pour identifier les erreurs 500"""
from app import create_app
from models.user import User
from models.role import Role
import traceback

app = create_app()
app.config['DEBUG'] = True
app.config['TESTING'] = True
app.config['PROPAGATE_EXCEPTIONS'] = True

with app.app_context():
    try:
        print("=== Test des routes CJ ===\n")
        
        # Récupérer l'utilisateur admin
        admin_user = User.query.join(Role).filter(Role.name == 'admin').first()
        
        if not admin_user:
            print("ERREUR: Aucun utilisateur admin trouvé")
        else:
            print(f"Utilisateur admin: {admin_user.username}\n")
            
            with app.test_client() as client:
                # Se connecter
                with client.session_transaction() as sess:
                    sess['_user_id'] = str(admin_user.id)
                    sess['_fresh'] = True
                
                # Test 1: /admin/cj/orders/
                print("=" * 60)
                print("Test 1: /admin/cj/orders/")
                print("=" * 60)
                try:
                    response = client.get('/admin/cj/orders/')
                    print(f"Status code: {response.status_code}")
                    if response.status_code == 500:
                        print("\n⚠ ERREUR 500")
                        print(response.data.decode('utf-8')[:1500])
                except Exception as e:
                    print(f"\n❌ EXCEPTION: {type(e).__name__}")
                    print(f"Message: {str(e)}")
                    print("\nTraceback:")
                    print(traceback.format_exc())
                
                print("\n")
                
                # Test 2: /admin/cj/dashboard
                print("=" * 60)
                print("Test 2: /admin/cj/dashboard")
                print("=" * 60)
                try:
                    response = client.get('/admin/cj/dashboard')
                    print(f"Status code: {response.status_code}")
                    if response.status_code == 500:
                        print("\n⚠ ERREUR 500")
                        print(response.data.decode('utf-8')[:1500])
                except Exception as e:
                    print(f"\n❌ EXCEPTION: {type(e).__name__}")
                    print(f"Message: {str(e)}")
                    print("\nTraceback:")
                    print(traceback.format_exc())
                    
    except Exception as e:
        print(f"\n=== ERREUR GÉNÉRALE ===")
        print(f"Type: {type(e).__name__}")
        print(f"Message: {str(e)}")
        print(traceback.format_exc())
