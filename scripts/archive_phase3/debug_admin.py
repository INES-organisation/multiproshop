from app import app
from extensions import db
from models.user import User
from models.role import Role

with app.app_context():
    print("=== DIAGNOSTIC ADMIN ===")
    
    # Vérifier les rôles
    roles = Role.query.all()
    print(f"Rôles disponibles: {len(roles)}")
    for role in roles:
        print(f"  - {role.name} (ID: {role.id})")
    
    # Vérifier l'utilisateur admin
    admin = User.query.filter_by(email='admin@multiproshop.com').first()
    if admin:
        print(f"\nUtilisateur admin trouvé:")
        print(f"  - Username: {admin.username}")
        print(f"  - Email: {admin.email}")
        print(f"  - Role ID: {admin.role_id}")
        if admin.role:
            print(f"  - Role name: {admin.role.name}")
        else:
            print(f"  - ERREUR: Aucun rôle associé!")
        
        # Test du mot de passe
        test_password = admin.check_password('admin123')
        print(f"  - Test mot de passe 'admin123': {test_password}")
    else:
        print("\nERREUR: Utilisateur admin non trouvé!")
    
    # Vérifier tous les utilisateurs
    users = User.query.all()
    print(f"\nTous les utilisateurs ({len(users)}):")
    for user in users:
        role_name = user.role.name if user.role else "Aucun rôle"
        print(f"  - {user.username} ({user.email}) - Rôle: {role_name}")
