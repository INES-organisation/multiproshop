"""
Migration pour créer la table webhook_log
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app import app
from extensions import db
from sqlalchemy import text, inspect

def table_exists(table_name):
    """Vérifier si une table existe"""
    inspector = inspect(db.engine)
    return table_name in inspector.get_table_names()

def run_migration():
    """Créer la table webhook_log"""
    with app.app_context():
        try:
            print("🔄 Création de la table webhook_log...")
            
            if table_exists('webhook_log'):
                print("  ✓ Table webhook_log existe déjà")
                return True
            
            # Créer la table
            sql = """
            CREATE TABLE webhook_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type VARCHAR(50) NOT NULL,
                payload TEXT,
                result TEXT,
                success BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
            
            db.session.execute(text(sql))
            
            # Créer les index
            db.session.execute(text('CREATE INDEX idx_webhook_log_event_type ON webhook_log(event_type)'))
            db.session.execute(text('CREATE INDEX idx_webhook_log_success ON webhook_log(success)'))
            db.session.execute(text('CREATE INDEX idx_webhook_log_created_at ON webhook_log(created_at)'))
            
            db.session.commit()
            
            print("✅ Table webhook_log créée avec succès!")
            print("\nStructure:")
            print("  - id (INTEGER PRIMARY KEY)")
            print("  - event_type (VARCHAR(50))")
            print("  - payload (TEXT)")
            print("  - result (TEXT)")
            print("  - success (BOOLEAN)")
            print("  - created_at (DATETIME)")
            print("\nIndex créés:")
            print("  - idx_webhook_log_event_type")
            print("  - idx_webhook_log_success")
            print("  - idx_webhook_log_created_at")
            
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
