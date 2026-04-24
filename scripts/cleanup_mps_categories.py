"""
Script de nettoyage : supprime tous les mappings et les sous-catégories MPS (N2, N3+)
Réassigne les produits vers leur catégorie parente N1 avant suppression.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'multiproshop.db')

def cleanup():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('PRAGMA foreign_keys = OFF')
    
    print("=" * 60)
    print("NETTOYAGE MPS : Mappings + Sous-catégories")
    print("=" * 60)
    
    # ETAPE 1 : Supprimer tous les mappings
    count = conn.execute('SELECT COUNT(*) FROM category_mapping').fetchone()[0]
    conn.execute('DELETE FROM category_mapping')
    print(f"\n[1/3] {count} mappings supprimés")
    
    # ETAPE 2 : Réassigner les produits des sous-catégories MPS vers N1
    # Construire la map parent pour les catégories MPS non-CJ
    rows = conn.execute(
        'SELECT id, parent_id, level FROM category WHERE cj_category_id IS NULL AND level >= 2 ORDER BY level DESC'
    ).fetchall()
    
    parent_map = {}
    for r in rows:
        parent_map[r[0]] = r[1]
    
    def find_n1(cat_id):
        visited = set()
        while cat_id in parent_map and cat_id not in visited:
            visited.add(cat_id)
            cat_id = parent_map[cat_id]
        return cat_id
    
    reassigned = 0
    for cat_id in parent_map:
        n1_id = find_n1(cat_id)
        if n1_id != cat_id:
            count = conn.execute(
                'UPDATE product SET category_id = ? WHERE category_id = ?',
                (n1_id, cat_id)
            ).rowcount
            reassigned += count
    
    print(f"[2/3] {reassigned} produits réassignés vers catégories N1")
    
    # ETAPE 3 : Supprimer les sous-catégories MPS (N2, N3+)
    # D'abord mettre parent_id à NULL pour éviter les contraintes FK
    conn.execute('UPDATE category SET parent_id = NULL WHERE cj_category_id IS NULL AND level >= 2')
    deleted = conn.execute('DELETE FROM category WHERE cj_category_id IS NULL AND level >= 2').rowcount
    print(f"[3/3] {deleted} sous-catégories MPS supprimées (N2, N3+)")
    
    conn.commit()
    
    # Vérification finale
    mps_count = conn.execute('SELECT COUNT(*) FROM category WHERE cj_category_id IS NULL').fetchone()[0]
    mapping_count = conn.execute('SELECT COUNT(*) FROM category_mapping').fetchone()[0]
    cj_count = conn.execute('SELECT COUNT(*) FROM category WHERE cj_category_id IS NOT NULL').fetchone()[0]
    
    print(f"\n{'=' * 60}")
    print(f"RÉSULTAT FINAL :")
    print(f"  Catégories MPS restantes (N1) : {mps_count}")
    print(f"  Catégories CJ : {cj_count}")
    print(f"  Mappings : {mapping_count}")
    print(f"{'=' * 60}")
    
    # Lister les catégories MPS restantes
    rows = conn.execute('SELECT id, name FROM category WHERE cj_category_id IS NULL ORDER BY name').fetchall()
    print("\nCatégories MPS N1 conservées :")
    for r in rows:
        print(f"  id={r[0]} | {r[1]}")
    
    conn.close()
    print("\nDONE")


if __name__ == '__main__':
    cleanup()
