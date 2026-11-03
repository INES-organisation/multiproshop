"""
Script pour tester la page /admin/orders avec authentification
"""
import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models.user import User
from flask import url_for

app = create_app('development')

with app.test_client() as client:
    with app.app_context():
        # Trouver l'utilisateur admin
        admin = User.query.filter_by(email='admin@multiproshop.com').first()
        
        if not admin:
            print("ERREUR: Utilisateur admin non trouvé")
            print("Créez un utilisateur admin d'abord")
            sys.exit(1)
        
        print(f"Admin trouvé: {admin.username} ({admin.email})")
        print(f"Role: {admin.role.name if admin.role else 'Aucun'}")
        
        # Se connecter
        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin.id)
            sess['_fresh'] = True
        
        print("\nTest de la route /admin/orders...")
        
        try:
            response = client.get('/admin/orders')
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                print("SUCCESS: Page chargée correctement")
                print(f"Taille de la réponse: {len(response.data)} bytes")
            elif response.status_code == 302:
                print(f"REDIRECT vers: {response.location}")
            elif response.status_code == 500:
                print("ERREUR 500 détectée!")
                print("\nContenu de la réponse:")
                print(response.data.decode('utf-8')[:1000])
            else:
                print(f"Status inattendu: {response.status_code}")
                
        except Exception as e:
            print(f"EXCEPTION: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
