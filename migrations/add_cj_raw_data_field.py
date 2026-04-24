"""
Migration: Ajouter champ cj_raw_data pour audit complet
Date: 31 Janvier 2026
Description: Ajoute un champ JSON pour stocker les données brutes CJ
"""
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from extensions import db
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def upgrade():
    """Ajouter le champ cj_raw_data aux tables Product et ProductVariant"""
    
    with app.app_context():
        logger.info("="*70)
        logger.info("🔄 MIGRATION: Ajout champ cj_raw_data")
        logger.info("="*70)
        
        try:
            # Ajouter colonne cj_raw_data à Product
            logger.info("\n📦 Ajout cj_raw_data à Product...")
            db.session.execute(text("""
                ALTER TABLE product 
                ADD COLUMN cj_raw_data TEXT NULL
            """))
            logger.info("✅ Colonne cj_raw_data ajoutée à Product")
            
            # Ajouter colonne cj_raw_data à ProductVariant
            logger.info("\n🎨 Ajout cj_raw_data à ProductVariant...")
            db.session.execute(text("""
                ALTER TABLE product_variant 
                ADD COLUMN cj_raw_data TEXT NULL
            """))
            logger.info("✅ Colonne cj_raw_data ajoutée à ProductVariant")
            
            # Ajouter colonne cj_last_sync à Product
            logger.info("\n📅 Ajout cj_last_sync à Product...")
            db.session.execute(text("""
                ALTER TABLE product 
                ADD COLUMN cj_last_sync DATETIME NULL
            """))
            logger.info("✅ Colonne cj_last_sync ajoutée à Product")
            
            db.session.commit()
            
            logger.info("\n" + "="*70)
            logger.info("✅ MIGRATION TERMINÉE AVEC SUCCÈS")
            logger.info("="*70)
            logger.info("\nChamps ajoutés:")
            logger.info("  - product.cj_raw_data (TEXT)")
            logger.info("  - product_variant.cj_raw_data (TEXT)")
            logger.info("  - product.cj_last_sync (DATETIME)")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"\n❌ ERREUR MIGRATION: {e}")
            
            # Vérifier si les colonnes existent déjà
            if "duplicate column name" in str(e).lower():
                logger.info("\n⚠️ Les colonnes existent déjà, migration ignorée")
                return True
            
            import traceback
            traceback.print_exc()
            return False


def downgrade():
    """Supprimer le champ cj_raw_data"""
    
    with app.app_context():
        logger.info("="*70)
        logger.info("🔄 ROLLBACK: Suppression champ cj_raw_data")
        logger.info("="*70)
        
        try:
            # SQLite ne supporte pas DROP COLUMN directement
            # Il faut recréer les tables
            logger.warning("\n⚠️ SQLite ne supporte pas DROP COLUMN")
            logger.warning("Pour rollback, il faut recréer les tables manuellement")
            
            return False
            
        except Exception as e:
            logger.error(f"\n❌ ERREUR ROLLBACK: {e}")
            return False


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Migration cj_raw_data')
    parser.add_argument('action', choices=['upgrade', 'downgrade'], 
                       help='Action à effectuer')
    
    args = parser.parse_args()
    
    if args.action == 'upgrade':
        success = upgrade()
        sys.exit(0 if success else 1)
    elif args.action == 'downgrade':
        success = downgrade()
        sys.exit(0 if success else 1)
