"""
Script pour vérifier et corriger le rôle admin
"""
from app import create_app
from extensions import db
from models.user import User
from models.role import Role

app = create_app()

with app.app_context():
    print("\n" + "="*70)
    print("🔍 VÉRIFICATION DES RÔLES ADMIN")
    print("="*70 + "\n")
    
    # Vérifier si le rôle 'admin' existe
    admin_role = Role.query.filter_by(name='admin').first()
    
    if not admin_role:
        print("❌ Le rôle 'admin' n'existe pas. Création...")
        admin_role = Role(name='admin', description='Administrateur')
        db.session.add(admin_role)
        db.session.commit()
        print("✅ Rôle 'admin' créé !")
    else:
        print(f"✅ Rôle 'admin' existe (ID: {admin_role.id})")
    
    # Lister tous les utilisateurs
    print("\n" + "-"*70)
    print("📋 LISTE DES UTILISATEURS")
    print("-"*70 + "\n")
    
    users = User.query.all()
    
    if not users:
        print("❌ Aucun utilisateur trouvé !")
    else:
        for user in users:
            role_name = user.role.name if user.role else "Aucun rôle"
            print(f"👤 {user.username} ({user.email})")
            print(f"   Rôle: {role_name}")
            print(f"   Role ID: {user.role_id}")
            print()
    
    # Proposer de définir un admin
    print("-"*70)
    print("🔧 CORRECTION DES RÔLES")
    print("-"*70 + "\n")
    
    # Chercher les utilisateurs sans rôle ou avec mauvais rôle
    users_to_fix = User.query.filter(
        (User.role_id == None) | (User.role_id != admin_role.id)
    ).all()
    
    if users_to_fix:
        print(f"⚠️  {len(users_to_fix)} utilisateur(s) n'ont pas le rôle admin\n")
        
        for user in users_to_fix:
            print(f"Définir {user.username} comme admin ? (o/n)")
            # Pour automatiser, on définit le premier utilisateur comme admin
            if user.id == 1:  # Premier utilisateur = admin par défaut
                user.role_id = admin_role.id
                db.session.commit()
                print(f"✅ {user.username} est maintenant admin !")
            else:
                print(f"⏭️  {user.username} ignoré (pas le premier utilisateur)")
    else:
        print("✅ Tous les utilisateurs ont le bon rôle !")
    
    print("\n" + "="*70)
    print("🎉 VÉRIFICATION TERMINÉE")
    print("="*70 + "\n")
    
    # Résumé final
    print("📊 RÉSUMÉ:")
    admin_users = User.query.join(Role).filter(Role.name == 'admin').all()
    print(f"   Administrateurs: {len(admin_users)}")
    for admin in admin_users:
        print(f"   - {admin.username} ({admin.email})")
    print()
