"""
Script pour migrer la table Order avec les nouveaux champs
"""
from app import app
from extensions import db
from models.order import Order, OrderItem
from models.user import User
from models.category import Category
import os
import shutil
from datetime import datetime

def backup_database():
    """Sauvegarder la base de données"""
    db_path = os.path.join(app.root_path, 'instance', 'multiproshop.db')
    if os.path.exists(db_path):
        backup_path = os.path.join(app.root_path, 'instance', f'multiproshop_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db')
        shutil.copy2(db_path, backup_path)
        print(f"✅ Sauvegarde créée: {backup_path}")
        return True
    return False

def migrate_orders():
    with app.app_context():
        print("\n" + "="*70)
        print("🔄 MIGRATION DE LA TABLE ORDER")
        print("="*70 + "\n")
        
        # Sauvegarder la BD
        print("📦 Sauvegarde de la base de données...")
        backup_database()
        
        try:
            # Supprimer l'ancienne table order
            print("\n🗑️  Suppression de l'ancienne table order...")
            db.session.execute(db.text('DROP TABLE IF EXISTS order_item'))
            db.session.execute(db.text('DROP TABLE IF EXISTS "order"'))
            db.session.commit()
            print("✅ Anciennes tables supprimées")
            
            # Recréer la table avec les nouveaux champs
            print("\n🔨 Création de la nouvelle table order...")
            db.create_all()
            print("✅ Nouvelle table créée")
            
            print("\n" + "="*70)
            print("✅ MIGRATION TERMINÉE AVEC SUCCÈS !")
            print("="*70)
            print("\nLa table Order a été migrée avec les nouveaux champs:")
            print("  • order_number (unique)")
            print("  • payment_status, payment_method")
            print("  • subtotal, shipping_cost, tax")
            print("  • customer_email, customer_phone")
            print("  • shipping_* (adresse complète)")
            print("  • shipping_method")
            print("  • customer_notes, admin_notes")
            print("  • paid_at, shipped_at, delivered_at")
            print("\n")
            
        except Exception as e:
            print(f"\n❌ ERREUR: {str(e)}")
            db.session.rollback()
            return False
        
        return True

if __name__ == "__main__":
    migrate_orders()
