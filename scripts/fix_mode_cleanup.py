"""
Supprimer les catégories MPS dupliquées directement sous Mode & Vêtements (id=52)
qui ne sont PAS les 3 N2 intermédiaires (Vêtements Homme, Vêtements Femme, Sacs & Chaussures).
Ces catégories ont été recréées par erreur par create_mps_subcategories.py.
Les bonnes catégories (avec produits) sont déjà sous les N2 intermédiaires.
"""
import sqlite3, os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'multiproshop.db')
MODE_MPS_ID = 52

def delete_tree(conn, cat_id, depth=0):
    """Supprimer récursivement une catégorie et ses enfants"""
    children = conn.execute(
        "SELECT id, name FROM category WHERE parent_id = ? AND cj_category_id IS NULL", (cat_id,)
    ).fetchall()
    
    for child_id, child_name in children:
        delete_tree(conn, child_id, depth + 1)
    
    # Vérifier qu'il n'y a pas de produits
    prod_count = conn.execute("SELECT COUNT(*) FROM product WHERE category_id = ?", (cat_id,)).fetchone()[0]
    if prod_count > 0:
        name = conn.execute("SELECT name FROM category WHERE id = ?", (cat_id,)).fetchone()[0]
        print(f"{'  ' * depth}⚠ SKIP id={cat_id} {name} ({prod_count} produits)")
        return 0
    
    # Supprimer le mapping associé
    conn.execute("DELETE FROM category_mapping WHERE mps_category_id = ?", (cat_id,))
    conn.execute("DELETE FROM category WHERE id = ?", (cat_id,))
    return 1

def run():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('PRAGMA foreign_keys = OFF')
    
    # IDs des 3 N2 intermédiaires à garder
    keep_ids = set()
    for name in ["Vêtements Homme", "Vêtements Femme", "Sacs & Chaussures"]:
        row = conn.execute(
            "SELECT id FROM category WHERE name = ? AND parent_id = ? AND cj_category_id IS NULL",
            (name, MODE_MPS_ID)
        ).fetchone()
        if row:
            keep_ids.add(row[0])
            print(f"  GARDER: {name} (id={row[0]})")
    
    # Catégories à supprimer
    wrong = conn.execute('''
        SELECT id, name FROM category 
        WHERE parent_id = ? AND cj_category_id IS NULL AND id NOT IN ({})
        ORDER BY name
    '''.format(','.join(str(i) for i in keep_ids)), (MODE_MPS_ID,)).fetchall()
    
    print(f"\n{len(wrong)} catégories dupliquées à supprimer:")
    
    total_deleted = 0
    for cat_id, cat_name in wrong:
        # Compter les enfants
        child_count = conn.execute(
            "SELECT COUNT(*) FROM category WHERE parent_id = ? AND cj_category_id IS NULL", (cat_id,)
        ).fetchone()[0]
        
        deleted = delete_tree(conn, cat_id)
        total_deleted += deleted
        print(f"  ✓ {cat_name} (id={cat_id}, {child_count} enfants) -> supprimé")
    
    conn.commit()
    
    print(f"\nTotal supprimé: {total_deleted} catégories (+ enfants)")
    
    # Vérification
    remaining = conn.execute(
        "SELECT id, name FROM category WHERE parent_id = ? AND cj_category_id IS NULL ORDER BY name",
        (MODE_MPS_ID,)
    ).fetchall()
    
    print(f"\nCatégories restantes sous Mode & Vêtements:")
    for r in remaining:
        n3_count = conn.execute(
            "SELECT COUNT(*) FROM category WHERE parent_id = ? AND cj_category_id IS NULL", (r[0],)
        ).fetchone()[0]
        print(f"  N2 {r[1]} (id={r[0]}, {n3_count} sous-catégories)")
    
    # Stats globales
    total_mps = conn.execute("SELECT COUNT(*) FROM category WHERE cj_category_id IS NULL").fetchone()[0]
    total_mappings = conn.execute("SELECT COUNT(*) FROM category_mapping").fetchone()[0]
    non_classe = conn.execute("SELECT COUNT(*) FROM product WHERE category_id = (SELECT id FROM category WHERE slug = 'non-classe')").fetchone()[0]
    print(f"\nStats: {total_mps} catégories MPS, {total_mappings} mappings, {non_classe} produits 'Non classé'")
    
    conn.close()
    print("DONE")

if __name__ == '__main__':
    run()
