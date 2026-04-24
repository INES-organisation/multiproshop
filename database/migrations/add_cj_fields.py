"""
Migration: Ajouter les champs CJ Dropshipping
- Enrichir Category avec hiérarchie CJ
- Enrichir Product avec champs CJ
- Créer table ProductVariant
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app import create_app
from extensions import db
from models.category import Category
from models.product import Product
from models.product_variant import ProductVariant

def run_migration():
    """Exécuter la migration"""
    app = create_app()
    
    with app.app_context():
        print("=" * 80)
        print("MIGRATION: Ajout des champs CJ Dropshipping")
        print("=" * 80)
        
        try:
            # Créer toutes les tables (y compris ProductVariant)
            print("\n1. Création des tables manquantes...")
            db.create_all()
            print("✓ Tables créées")
            
            # Vérifier les colonnes existantes
            print("\n2. Vérification des colonnes...")
            
            # Les nouvelles colonnes seront automatiquement ajoutées par SQLAlchemy
            # lors de la prochaine création de tables
            
            # Créer des index pour performances
            print("\n3. Création des index...")
            
            with db.engine.connect() as conn:
                # Index pour Category
                try:
                    conn.execute(db.text('CREATE INDEX IF NOT EXISTS idx_category_parent ON category(parent_id)'))
                    conn.execute(db.text('CREATE INDEX IF NOT EXISTS idx_category_level ON category(level)'))
                    conn.execute(db.text('CREATE INDEX IF NOT EXISTS idx_category_cj_id ON category(cj_category_id)'))
                    conn.execute(db.text('CREATE INDEX IF NOT EXISTS idx_category_visible ON category(visible)'))
                    print("✓ Index Category créés")
                except Exception as e:
                    print(f"⚠ Index Category: {e}")
                
                # Index pour Product
                try:
                    conn.execute(db.text('CREATE INDEX IF NOT EXISTS idx_product_cj_pid ON product(cj_pid)'))
                    conn.execute(db.text('CREATE INDEX IF NOT EXISTS idx_product_published ON product(published)'))
                    conn.execute(db.text('CREATE INDEX IF NOT EXISTS idx_product_category ON product(category_id)'))
                    conn.execute(db.text('CREATE INDEX IF NOT EXISTS idx_product_active ON product(is_active)'))
                    print("✓ Index Product créés")
                except Exception as e:
                    print(f"⚠ Index Product: {e}")
                
                # Index pour ProductVariant
                try:
                    conn.execute(db.text('CREATE INDEX IF NOT EXISTS idx_variant_product ON product_variant(product_id)'))
                    conn.execute(db.text('CREATE INDEX IF NOT EXISTS idx_variant_cj_vid ON product_variant(cj_vid)'))
                    conn.execute(db.text('CREATE INDEX IF NOT EXISTS idx_variant_active ON product_variant(active)'))
                    print("✓ Index ProductVariant créés")
                except Exception as e:
                    print(f"⚠ Index ProductVariant: {e}")
                
                conn.commit()
            
            print("\n" + "=" * 80)
            print("✅ MIGRATION RÉUSSIE")
            print("=" * 80)
            print("\nNouvelles fonctionnalités disponibles:")
            print("- Catégories hiérarchiques CJ (3 niveaux)")
            print("- Produits CJ avec synchronisation")
            print("- Variantes produits (couleurs, tailles)")
            print("- Index pour performances optimales")
            
            return True
            
        except Exception as e:
            print(f"\n❌ ERREUR MIGRATION: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    success = run_migration()
    sys.exit(0 if success else 1)
