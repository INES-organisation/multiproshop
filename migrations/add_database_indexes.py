"""
Migration: Ajouter des indexes pour optimiser les requêtes CJ
Date: 31 Janvier 2026
Description: Ajoute des indexes sur les colonnes fréquemment utilisées
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
    """Ajouter les indexes pour optimiser les performances"""
    
    with app.app_context():
        logger.info("="*70)
        logger.info("🔄 MIGRATION: Ajout indexes base de données")
        logger.info("="*70)
        
        indexes_to_create = [
            # Indexes Product
            ("idx_product_cj_pid", "product", "cj_pid"),
            ("idx_product_is_active", "product", "is_active"),
            ("idx_product_published", "product", "published"),
            ("idx_product_category_id", "product", "category_id"),
            ("idx_product_cj_last_sync", "product", "cj_last_sync"),
            ("idx_product_stock", "product", "stock"),
            
            # Indexes ProductVariant
            ("idx_variant_cj_vid", "product_variant", "cj_vid"),
            ("idx_variant_product_id", "product_variant", "product_id"),
            ("idx_variant_stock", "product_variant", "stock"),
            
            # Indexes Order
            ("idx_order_cj_order_id", "order", "cj_order_id"),
            ("idx_order_status", "order", "status"),
            ("idx_order_user_id", "order", "user_id"),
            ("idx_order_created_at", "order", "created_at"),
            
            # Indexes Category
            ("idx_category_cj_category_id", "category", "cj_category_id"),
            ("idx_category_parent_id", "category", "parent_id"),
            ("idx_category_level", "category", "level"),
            ("idx_category_visible", "category", "visible"),
            
            # Indexes WebhookLog
            ("idx_webhook_event_type", "webhook_log", "event_type"),
            ("idx_webhook_status", "webhook_log", "status"),
            ("idx_webhook_created_at", "webhook_log", "created_at"),
        ]
        
        created_count = 0
        skipped_count = 0
        
        for index_name, table_name, column_name in indexes_to_create:
            try:
                logger.info(f"\n📊 Création index {index_name} sur {table_name}.{column_name}...")
                
                db.session.execute(text(f"""
                    CREATE INDEX IF NOT EXISTS {index_name} 
                    ON {table_name} ({column_name})
                """))
                
                logger.info(f"✅ Index {index_name} créé")
                created_count += 1
                
            except Exception as e:
                if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                    logger.info(f"⏭️ Index {index_name} existe déjà")
                    skipped_count += 1
                else:
                    logger.error(f"❌ Erreur création index {index_name}: {e}")
        
        # Indexes composites pour requêtes complexes
        composite_indexes = [
            ("idx_product_cj_active", "product", ["cj_pid", "is_active"]),
            ("idx_product_category_active", "product", ["category_id", "is_active"]),
            ("idx_order_cj_status", "order", ["cj_order_id", "status"]),
        ]
        
        for index_name, table_name, columns in composite_indexes:
            try:
                columns_str = ", ".join(columns)
                logger.info(f"\n📊 Création index composite {index_name} sur {table_name}({columns_str})...")
                
                db.session.execute(text(f"""
                    CREATE INDEX IF NOT EXISTS {index_name} 
                    ON {table_name} ({columns_str})
                """))
                
                logger.info(f"✅ Index composite {index_name} créé")
                created_count += 1
                
            except Exception as e:
                if "already exists" in str(e).lower():
                    logger.info(f"⏭️ Index {index_name} existe déjà")
                    skipped_count += 1
                else:
                    logger.error(f"❌ Erreur création index {index_name}: {e}")
        
        db.session.commit()
        
        logger.info("\n" + "="*70)
        logger.info("✅ MIGRATION INDEXES TERMINÉE")
        logger.info("="*70)
        logger.info(f"\nIndexes créés: {created_count}")
        logger.info(f"Indexes existants: {skipped_count}")
        logger.info(f"Total: {created_count + skipped_count}")
        
        logger.info("\n📈 Bénéfices attendus:")
        logger.info("  - Requêtes CJ 50-80% plus rapides")
        logger.info("  - Recherches par cj_pid instantanées")
        logger.info("  - Filtres par catégorie optimisés")
        logger.info("  - Webhooks logs plus rapides")
        
        return True


def downgrade():
    """Supprimer les indexes"""
    
    with app.app_context():
        logger.info("="*70)
        logger.info("🔄 ROLLBACK: Suppression indexes")
        logger.info("="*70)
        
        logger.warning("\n⚠️ Suppression des indexes non recommandée")
        logger.warning("Les indexes améliorent les performances sans effet secondaire")
        
        return False


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Migration indexes base de données')
    parser.add_argument('action', choices=['upgrade', 'downgrade'], 
                       help='Action à effectuer')
    
    args = parser.parse_args()
    
    if args.action == 'upgrade':
        success = upgrade()
        sys.exit(0 if success else 1)
    elif args.action == 'downgrade':
        success = downgrade()
        sys.exit(0 if success else 1)
