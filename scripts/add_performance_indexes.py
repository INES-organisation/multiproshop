"""
Script pour ajouter des index de performance à la base de données
Optimise les requêtes sur les catégories et produits
"""
import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from extensions import db
from sqlalchemy import text

app = create_app(os.getenv('FLASK_ENV', 'development'))

with app.app_context():
    print("\n" + "="*70)
    print("AJOUT DES INDEX DE PERFORMANCE")
    print("="*70 + "\n")
    
    try:
        # Index pour les catégories - optimise les requêtes de la sidebar
        print("1. Ajout index sur category(level, is_active)...")
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_category_level_active 
            ON category(level, is_active)
        """))
        print("   ✅ Index idx_category_level_active créé")
        
        print("\n2. Ajout index sur category(parent_id)...")
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_category_parent_id 
            ON category(parent_id)
        """))
        print("   ✅ Index idx_category_parent_id créé")
        
        print("\n3. Ajout index sur category(order)...")
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_category_order 
            ON category("order")
        """))
        print("   ✅ Index idx_category_order créé")
        
        # Index pour les produits - optimise les requêtes de listing
        print("\n4. Ajout index sur product(category_id, is_active)...")
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_product_category_active 
            ON product(category_id, is_active)
        """))
        print("   ✅ Index idx_product_category_active créé")
        
        print("\n5. Ajout index sur product(published)...")
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_product_published 
            ON product(published)
        """))
        print("   ✅ Index idx_product_published créé")
        
        print("\n6. Ajout index sur product(cj_pid)...")
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_product_cj_pid 
            ON product(cj_pid)
        """))
        print("   ✅ Index idx_product_cj_pid créé")
        
        # Commit tous les changements
        db.session.commit()
        
        print("\n" + "="*70)
        print("✅ TOUS LES INDEX DE PERFORMANCE ONT ÉTÉ AJOUTÉS AVEC SUCCÈS")
        print("="*70)
        print("\n📊 Gains attendus:")
        print("   - Requêtes catégories: 20-30% plus rapides")
        print("   - Requêtes produits: 20-30% plus rapides")
        print("   - Sidebar: Chargement optimisé\n")
        
    except Exception as e:
        print(f"\n❌ Erreur lors de la création des index: {e}")
        db.session.rollback()
