"""Test de la route admin pour identifier l'erreur 500"""
from app import create_app
from models.user import User
from models.role import Role
from models.product import Product
import traceback

app = create_app()

with app.app_context():
    try:
        print("Test de la route admin dashboard...")
        
        # Vérifier si les modèles sont accessibles
        print(f"Nombre de produits: {Product.query.count()}")
        print(f"Nombre d'utilisateurs: {User.query.count()}")
        
        # Tester l'import de la route
        from routes.admin import dashboard
        print("Route dashboard importée avec succès")
        
        # Simuler un appel à la route
        with app.test_client() as client:
            # Créer un utilisateur admin pour le test
            admin_role = Role.query.filter_by(name='admin').first()
            if not admin_role:
                print("ERREUR: Rôle admin non trouvé dans la base de données")
            else:
                print(f"Rôle admin trouvé: {admin_role.name}")
                
                # Vérifier s'il y a un utilisateur admin
                admin_user = User.query.join(Role).filter(Role.name == 'admin').first()
                if admin_user:
                    print(f"Utilisateur admin trouvé: {admin_user.username}")
                else:
                    print("Aucun utilisateur admin trouvé")
            
            # Tester l'accès à la route (sans authentification)
            response = client.get('/admin/')
            print(f"Status code: {response.status_code}")
            if response.status_code == 500:
                print("ERREUR 500 détectée!")
                print(f"Réponse: {response.data.decode('utf-8')[:500]}")
            elif response.status_code == 302:
                print(f"Redirection vers: {response.location}")
            
    except Exception as e:
        print(f"ERREUR: {e}")
        print(traceback.format_exc())
