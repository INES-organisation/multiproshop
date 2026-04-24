"""
Recréer la base de données avec le bon schéma
"""
import os
from app import app
from extensions import db
from models.user import User
from models.role import Role
from models.category import Category
from models.product import Product

def recreate_database():
    with app.app_context():
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        
        print(f"\n{'='*70}")
        print(f"🔄 RECRÉATION DE LA BASE DE DONNÉES")
        print(f"{'='*70}")
        print(f"📁 Chemin: {db_path}")
        
        # Sauvegarder l'ancienne BD si elle existe
        if os.path.exists(db_path):
            import time
            backup_path = db_path + f'.old_{int(time.time())}'
            try:
                os.rename(db_path, backup_path)
                print(f"💾 Ancienne BD renommée: {backup_path}")
            except:
                print(f"⚠️  Impossible de renommer l'ancienne BD (peut-être déjà supprimée)")
        else:
            print(f"ℹ️  Aucune BD existante, création d'une nouvelle")
        
        # Créer toutes les tables
        db.create_all()
        print(f"✅ Nouvelles tables créées")
        
        # Créer les rôles
        admin_role = Role(name='admin')
        user_role = Role(name='user')
        db.session.add(admin_role)
        db.session.add(user_role)
        db.session.commit()
        print(f"✅ Rôles créés: admin, user")
        
        # Créer un utilisateur admin
        admin_user = User(
            username='admin',
            email='admin@multiproshop.com'
        )
        admin_user.set_password('admin123')
        admin_user.role = admin_role
        db.session.add(admin_user)
        db.session.commit()
        print(f"✅ Utilisateur admin créé (login: admin / password: admin123)")
        
        # Créer les 17 catégories harmonisées
        categories = [
            (1, 'Électronique', 'TV, Audio, Vidéo, Home cinéma, Appareils photo, Casques audio, Jeux vidéo, Enceintes'),
            (2, 'Informatique', 'Ordinateurs, PC portables, Tablettes, Moniteurs, Réseaux, Composants, Stockage, PC Gamer'),
            (3, 'Téléphones & Accessoires', 'Smartphones iOS, Android, Coques, Casques, Câbles de charge, Cartes mémoire'),
            (4, 'Vêtements & Mode', 'Mode Homme, Femme, Enfant, Chaussures, Accessoires vestimentaires'),
            (5, 'Maison & Jardin', 'Meubles, Décoration, Électroménager, Cuisine, Jardin, Plantes'),
            (6, 'Santé & Beauté', 'Soins, Bien-être, Cosmétiques, Parfums, Produits de beauté, Hygiène'),
            (7, 'Bijoux & Montres', 'Bijoux, Montres, Joaillerie, Accessoires de luxe'),
            (8, 'Bébés & Puériculture', 'Articles pour bébés, Poussettes, Vêtements bébé, Jouets premier âge, Maternité'),
            (9, 'Sports & Loisirs', 'Équipements sportifs, Fitness, Camping, Randonnée, Vélo, Sports nautiques'),
            (10, 'Livres & Papeterie', 'Livres, Romans, BD, Fournitures de bureau, Papeterie, Carterie'),
            (11, 'Jeux & Jouets', 'Jeux vidéo, Consoles, Jouets enfants, Jeux de société, Figurines, Loisirs créatifs'),
            (12, 'Auto & Moto', 'Pièces automobiles, Accessoires auto, Moto, Équipements, Entretien véhicules'),
            (13, 'Bricolage & Outillage', 'Outils, Outillage électroportatif, Quincaillerie, Matériaux, Rénovation'),
            (14, 'Alimentation & Boissons', 'Épicerie, Produits frais, Boissons, Vins, Produits du terroir, Gourmandises'),
            (15, 'Animalerie', 'Nourriture animaux, Accessoires chiens, chats, Aquariophilie, Oiseaux, Rongeurs'),
            (16, 'Culture & Divertissement', 'Musique, Films, Séries, Instruments de musique, Billetterie spectacles'),
            (17, 'Services & Cartes Cadeaux', 'Cartes cadeaux, Services, Abonnements, Bons plans, Offres spéciales')
        ]
        
        for cat_id, name, description in categories:
            category = Category(name=name, description=description)
            db.session.add(category)
        
        db.session.commit()
        print(f"✅ 17 catégories créées")
        
        print(f"\n{'='*70}")
        print(f"✅ BASE DE DONNÉES RECRÉÉE AVEC SUCCÈS !")
        print(f"{'='*70}")
        print(f"\n📊 RÉSUMÉ :")
        print(f"   • Rôles: {Role.query.count()}")
        print(f"   • Utilisateurs: {User.query.count()}")
        print(f"   • Catégories: {Category.query.count()}")
        print(f"\n🔐 CONNEXION ADMIN :")
        print(f"   • Username: admin")
        print(f"   • Password: admin123")
        print(f"   • URL: http://127.0.0.1:5000/auth/admin-login")
        print(f"\n{'='*70}\n")

if __name__ == '__main__':
    recreate_database()
