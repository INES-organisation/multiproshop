"""
Script d'analyse des performances de la base de données
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from extensions import db
from sqlalchemy import text
import time

app = create_app()

def analyze_database():
    """Analyser les performances de la base de données"""
    with app.app_context():
        print("="*70)
        print("🔍 ANALYSE DES PERFORMANCES DE LA BASE DE DONNÉES")
        print("="*70)
        print()
        
        # 1. Taille de la base de données
        print("📊 TAILLE DE LA BASE DE DONNÉES")
        print("-"*70)
        
        tables = [
            'product', 'category', 'user', 'order', 'order_item',
            'api_provider', 'product_source', 'sync_log'
        ]
        
        for table in tables:
            try:
                result = db.session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                print(f"  {table:20} : {count:>6} lignes")
            except Exception as e:
                print(f"  {table:20} : Erreur - {str(e)[:30]}")
        
        print()
        
        # 2. Indexes existants
        print("🔑 INDEXES EXISTANTS")
        print("-"*70)
        
        # SQLite - Liste des indexes
        result = db.session.execute(text(
            "SELECT name, tbl_name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'"
        ))
        
        indexes = result.fetchall()
        print(f"  Total : {len(indexes)} indexes")
        
        for idx_name, table_name in indexes[:10]:  # Afficher les 10 premiers
            print(f"  - {idx_name} sur {table_name}")
        
        if len(indexes) > 10:
            print(f"  ... et {len(indexes) - 10} autres")
        
        print()
        
        # 3. Test de performance des requêtes
        print("⚡ TEST DE PERFORMANCE DES REQUÊTES")
        print("-"*70)
        
        queries = [
            ("SELECT * FROM product LIMIT 10", "Récupérer 10 produits"),
            ("SELECT * FROM product WHERE is_active = 1 LIMIT 10", "Produits actifs"),
            ("SELECT p.*, c.name FROM product p LEFT JOIN category c ON p.category_id = c.id LIMIT 10", "Produits avec catégories"),
            ("SELECT COUNT(*) FROM product", "Compter produits"),
            ("SELECT COUNT(*) FROM order", "Compter commandes"),
        ]
        
        for query, description in queries:
            start = time.time()
            try:
                db.session.execute(text(query))
                elapsed = (time.time() - start) * 1000  # en ms
                status = "✅" if elapsed < 10 else "⚠️" if elapsed < 50 else "❌"
                print(f"  {status} {description:40} : {elapsed:>6.2f} ms")
            except Exception as e:
                print(f"  ❌ {description:40} : Erreur")
        
        print()
        
        # 4. Recommandations
        print("💡 RECOMMANDATIONS")
        print("-"*70)
        
        # Vérifier si les indexes critiques existent
        critical_indexes = {
            'idx_product_category': 'product',
            'idx_product_active': 'product',
            'idx_order_user': 'order',
            'idx_order_status': 'order',
        }
        
        existing_idx_names = [idx[0] for idx in indexes]
        missing_indexes = []
        
        for idx_name, table in critical_indexes.items():
            if idx_name not in existing_idx_names:
                missing_indexes.append((idx_name, table))
        
        if missing_indexes:
            print("  ⚠️  Indexes manquants :")
            for idx_name, table in missing_indexes:
                print(f"     - {idx_name} sur table {table}")
            print()
            print("  💡 Exécuter : python scripts/add_database_indexes.py")
        else:
            print("  ✅ Tous les indexes critiques sont présents")
        
        print()
        
        # 5. Statistiques globales
        print("📈 STATISTIQUES GLOBALES")
        print("-"*70)
        
        try:
            # Nombre total de produits
            result = db.session.execute(text("SELECT COUNT(*) FROM product"))
            total_products = result.scalar()
            
            # Produits actifs
            result = db.session.execute(text("SELECT COUNT(*) FROM product WHERE is_active = 1"))
            active_products = result.scalar()
            
            # Nombre de catégories
            result = db.session.execute(text("SELECT COUNT(*) FROM category"))
            total_categories = result.scalar()
            
            # Nombre de commandes
            result = db.session.execute(text("SELECT COUNT(*) FROM 'order'"))
            total_orders = result.scalar()
            
            print(f"  Produits totaux    : {total_products:>6}")
            print(f"  Produits actifs    : {active_products:>6} ({active_products*100//max(total_products,1)}%)")
            print(f"  Catégories         : {total_categories:>6}")
            print(f"  Commandes          : {total_orders:>6}")
            
        except Exception as e:
            print(f"  Erreur lors de la récupération des stats : {e}")
        
        print()
        print("="*70)
        print("✅ Analyse terminée")
        print("="*70)


if __name__ == '__main__':
    analyze_database()
