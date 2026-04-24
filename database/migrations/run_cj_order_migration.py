"""
Script pour exécuter la migration des champs CJ Order
Compatible avec SQLite
"""
import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app import app
from extensions import db
from sqlalchemy import text, inspect

def column_exists(table_name, column_name):
    """Vérifier si une colonne existe dans une table"""
    inspector = inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns

def run_migration():
    """Exécuter la migration"""
    with app.app_context():
        try:
            print("🔄 Début de la migration CJ Order...")
            
            # Liste des colonnes à ajouter à la table order
            order_columns = [
                ('cj_order_id', 'VARCHAR(100)'),
                ('cj_tracking_number', 'VARCHAR(100)'),
                ('cj_status', 'VARCHAR(50)'),
                ('cj_logistics_name', 'VARCHAR(100)')
            ]
            
            # Ajouter les colonnes à la table order
            for col_name, col_type in order_columns:
                if not column_exists('order', col_name):
                    print(f"  Ajout de order.{col_name}...")
                    db.session.execute(text(f'ALTER TABLE "order" ADD COLUMN {col_name} {col_type}'))
                else:
                    print(f"  ✓ order.{col_name} existe déjà")
            
            # Ajouter variant_id à order_item
            if not column_exists('order_item', 'variant_id'):
                print(f"  Ajout de order_item.variant_id...")
                db.session.execute(text('ALTER TABLE order_item ADD COLUMN variant_id INTEGER'))
            else:
                print(f"  ✓ order_item.variant_id existe déjà")
            
            db.session.commit()
            
            print("\n✅ Migration CJ Order terminée avec succès!")
            print("\nChamps ajoutés/vérifiés:")
            print("  - order.cj_order_id")
            print("  - order.cj_tracking_number")
            print("  - order.cj_status")
            print("  - order.cj_logistics_name")
            print("  - order_item.variant_id")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de la migration: {e}")
            db.session.rollback()
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    success = run_migration()
    sys.exit(0 if success else 1)
