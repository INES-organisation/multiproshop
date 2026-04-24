"""
Script pour mettre à jour la base de données avec les nouveaux champs Product
"""
import os
import shutil
from datetime import datetime
from app import app
from extensions import db

def backup_database():
    """Créer une sauvegarde de la base de données"""
    db_path = os.path.join('instance', 'multiproshop.db')
    if os.path.exists(db_path):
        backup_path = os.path.join('instance', f'multiproshop_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db')
        shutil.copy2(db_path, backup_path)
        print(f"✅ Sauvegarde créée: {backup_path}")
        return True
    return False

def upgrade_database():
    with app.app_context():
        print("\n" + "="*70)
        print("🔄 MISE À JOUR DE LA BASE DE DONNÉES")
        print("="*70 + "\n")
        
        # Sauvegarder
        print("📦 Création d'une sauvegarde...")
        backup_database()
        
        print("\n📝 Recréation des tables...")
        
        # Supprimer et recréer toutes les tables
        db.drop_all()
        db.create_all()
        
        print("✅ Tables recréées avec succès !")
        
        # Recréer les rôles
        print("\n👥 Recréation des rôles...")
        from models.role import Role
        
        roles_data = [
            {'name': 'admin', 'description': 'Administrateur'},
            {'name': 'user', 'description': 'Utilisateur'},
            {'name': 'supplier', 'description': 'Fournisseur'}
        ]
        
        for role_data in roles_data:
            role = Role.query.filter_by(name=role_data['name']).first()
            if not role:
                role = Role(**role_data)
                db.session.add(role)
                print(f"   ✓ Rôle '{role_data['name']}' créé")
        
        db.session.commit()
        
        # Recréer l'admin
        print("\n👤 Recréation de l'utilisateur admin...")
        from models.user import User
        
        admin_role = Role.query.filter_by(name='admin').first()
        admin = User.query.filter_by(email='admin@multiproshop.com').first()
        
        if not admin:
            admin = User(
                username='admin',
                email='admin@multiproshop.com',
                role_id=admin_role.id
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("   ✓ Admin créé (email: admin@multiproshop.com, mot de passe: admin123)")
        else:
            print("   ℹ️  Admin existe déjà")
        
        print("\n✅ Mise à jour terminée avec succès !")
        print("\n⚠️  ATTENTION: Les produits existants ont été supprimés.")
        print("   Utilisez le script 'add_sample_products.py' pour ajouter des produits de test.")
        print("="*70 + "\n")

if __name__ == "__main__":
    upgrade_database()
