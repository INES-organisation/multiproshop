"""
Migration vers le système hiérarchique de catégories
"""
import os
from app import app
from extensions import db

# Supprimer et recréer la BD
with app.app_context():
    db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
    
    # Recréer toutes les tables avec le nouveau schéma
    db.create_all()
    print("✅ Nouvelles tables créées avec schéma hiérarchique")
    print("\n📊 La base de données est prête pour les catégories hiérarchiques")
    print("🔄 Vous pouvez maintenant ajouter les catégories")
