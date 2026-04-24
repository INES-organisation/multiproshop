"""
Script de vérification des mappings CJ Dropshipping
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'instance', 'multiproshop.db')

def verify_mappings():
    """Vérifier les mappings créés"""
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("="*80)
    print("VÉRIFICATION DES MAPPINGS CJ DROPSHIPPING")
    print("="*80)
    
    # 1. Statistiques générales
    print("\n1. STATISTIQUES GÉNÉRALES")
    print("-" * 80)
    
    cursor.execute("SELECT COUNT(*) FROM category")
    total_categories = cursor.fetchone()[0]
    print(f"Total catégories MPS: {total_categories}")
    
    cursor.execute("SELECT COUNT(*) FROM category WHERE level = 1")
    level1 = cursor.fetchone()[0]
    print(f"  - Niveau 1 (principales): {level1}")
    
    cursor.execute("SELECT COUNT(*) FROM category WHERE level = 2")
    level2 = cursor.fetchone()[0]
    print(f"  - Niveau 2 (sous-catégories): {level2}")
    
    cursor.execute("SELECT COUNT(*) FROM category WHERE level = 3")
    level3 = cursor.fetchone()[0]
    print(f"  - Niveau 3 (sous-sous-catégories): {level3}")
    
    cursor.execute("""
        SELECT COUNT(*) 
        FROM category_mapping cm
        JOIN api_provider ap ON cm.provider_id = ap.id
        WHERE ap.slug = 'cj-dropshipping'
    """)
    total_mappings = cursor.fetchone()[0]
    print(f"\nTotal mappings CJ: {total_mappings}")
    
    # 2. Exemples de mappings
    print("\n2. EXEMPLES DE MAPPINGS")
    print("-" * 80)
    
    cursor.execute("""
        SELECT 
            cm.external_category_name,
            cm.external_category_path,
            c.name as mps_category,
            c.level
        FROM category_mapping cm
        JOIN category c ON cm.mps_category_id = c.id
        JOIN api_provider ap ON cm.provider_id = ap.id
        WHERE ap.slug = 'cj-dropshipping'
        ORDER BY RANDOM()
        LIMIT 10
    """)
    
    for i, row in enumerate(cursor.fetchall(), 1):
        print(f"\n{i}. {row[0]}")
        print(f"   CJ Path: {row[1]}")
        print(f"   MPS Category: {row[2]} (Level {row[3]})")
    
    # 3. Catégories principales MPS avec comptage
    print("\n3. CATÉGORIES PRINCIPALES MPS (avec nombre de sous-catégories)")
    print("-" * 80)
    
    cursor.execute("""
        SELECT 
            c.name,
            COUNT(DISTINCT c2.id) as subcategories,
            COUNT(DISTINCT cm.id) as mappings
        FROM category c
        LEFT JOIN category c2 ON c2.parent_id = c.id
        LEFT JOIN category_mapping cm ON cm.mps_category_id = c.id OR cm.mps_category_id = c2.id
        WHERE c.level = 1
        GROUP BY c.id, c.name
        ORDER BY c.name
    """)
    
    for row in cursor.fetchall():
        print(f"  • {row[0]}: {row[1]} sous-catégories, {row[2]} mappings")
    
    conn.close()
    
    print("\n" + "="*80)
    print("✅ Vérification terminée")
    print("="*80)

if __name__ == '__main__':
    verify_mappings()
