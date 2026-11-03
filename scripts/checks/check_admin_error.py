"""Test détaillé pour identifier l'erreur 500 sur /admin/"""
from app import create_app
from models.user import User
from models.role import Role
from flask import Flask
import traceback
import sys

app = create_app()

# Activer le mode debug pour voir les erreurs
app.config['DEBUG'] = True
app.config['TESTING'] = True

with app.app_context():
    try:
        print("=== Test de la route /admin/ ===\n")
        
        # Récupérer l'utilisateur admin
        admin_user = User.query.join(Role).filter(Role.name == 'admin').first()
        
        if not admin_user:
            print("ERREUR: Aucun utilisateur admin trouvé")
            sys.exit(1)
        
        print(f"Utilisateur admin: {admin_user.username} (ID: {admin_user.id})")
        print(f"Rôle: {admin_user.role.name if admin_user.role else 'None'}\n")
        
        # Créer un client de test
        with app.test_client() as client:
            # Se connecter en tant qu'admin
            with client.session_transaction() as sess:
                sess['_user_id'] = str(admin_user.id)
                sess['_fresh'] = True
            
            print("Tentative d'accès à /admin/...")
            
            # Capturer les erreurs avec propagate_exceptions
            app.config['PROPAGATE_EXCEPTIONS'] = True
            
            try:
                response = client.get('/admin/', follow_redirects=False)
                print(f"Status code: {response.status_code}")
                
                if response.status_code == 500:
                    print("\n=== ERREUR 500 DÉTECTÉE ===")
                    print("Contenu de la réponse:")
                    print(response.data.decode('utf-8')[:2000])
                elif response.status_code == 200:
                    print("\n✓ Succès! La page se charge correctement")
                    # Vérifier si c'est bien le dashboard admin
                    html = response.data.decode('utf-8')
                    if 'Dashboard Admin' in html or 'admin-content' in html:
                        print("✓ Le template admin est bien rendu")
                    else:
                        print("⚠ Le template rendu n'est pas le dashboard admin")
                elif response.status_code == 302:
                    print(f"Redirection vers: {response.location}")
                else:
                    print(f"Code inattendu: {response.status_code}")
                    
            except Exception as e:
                print(f"\n=== EXCEPTION LORS DE LA REQUÊTE ===")
                print(f"Type: {type(e).__name__}")
                print(f"Message: {str(e)}")
                print("\n=== TRACEBACK COMPLET ===")
                print(traceback.format_exc())
                
    except Exception as e:
        print(f"\n=== ERREUR GÉNÉRALE ===")
        print(f"Type: {type(e).__name__}")
        print(f"Message: {str(e)}")
        print("\n=== TRACEBACK ===")
        print(traceback.format_exc())
