"""
Nettoyer les noms incohérents dans Mode & Vêtements :
- Sous "Vêtements Homme" : supprimer les N4 avec "Femme" dans le nom
- Sous "Vêtements Femme" : supprimer les N4 avec "Homme" dans le nom
- Sous "Accessoires Homme" : renommer les doublons génériques
- Nettoyer les catégories vides et incohérentes
"""
import sqlite3, json, os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'multiproshop.db')

def run():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('PRAGMA foreign_keys = OFF')
    
    provider_id = conn.execute("SELECT id FROM api_provider WHERE slug = 'cj-dropshipping'").fetchone()[0]
    
    VET_HOMME_ID = conn.execute("SELECT id FROM category WHERE name = 'Vêtements Homme' AND parent_id = 52 AND cj_category_id IS NULL").fetchone()[0]
    VET_FEMME_ID = conn.execute("SELECT id FROM category WHERE name = 'Vêtements Femme' AND parent_id = 52 AND cj_category_id IS NULL").fetchone()[0]
    SACS_ID = conn.execute("SELECT id FROM category WHERE name = 'Sacs & Chaussures' AND parent_id = 52 AND cj_category_id IS NULL").fetchone()[0]
    
    print(f"Vêtements Homme: id={VET_HOMME_ID}")
    print(f"Vêtements Femme: id={VET_FEMME_ID}")
    print(f"Sacs & Chaussures: id={SACS_ID}")
    
    # 1. Collecter toutes les catégories N3 sous Vêtements Homme
    homme_n3s = conn.execute(
        "SELECT id, name FROM category WHERE parent_id = ? AND cj_category_id IS NULL", (VET_HOMME_ID,)
    ).fetchall()
    
    # 2. Collecter toutes les catégories N3 sous Vêtements Femme
    femme_n3s = conn.execute(
        "SELECT id, name FROM category WHERE parent_id = ? AND cj_category_id IS NULL", (VET_FEMME_ID,)
    ).fetchall()
    
    deleted_total = 0
    
    # Nettoyer sous Vêtements Homme : supprimer N4 avec "Femme" dans le nom
    print(f"\n=== Nettoyage sous Vêtements Homme ===")
    for n3_id, n3_name in homme_n3s:
        n4s = conn.execute(
            "SELECT id, name FROM category WHERE parent_id = ? AND cj_category_id IS NULL", (n3_id,)
        ).fetchall()
        
        for n4_id, n4_name in n4s:
            # Supprimer si le nom contient "Femme" et qu'on est sous Homme
            if 'Femme' in n4_name and 'Homme' not in n4_name:
                # Vérifier si des produits sont liés
                prod_count = conn.execute("SELECT COUNT(*) FROM product WHERE category_id = ?", (n4_id,)).fetchone()[0]
                if prod_count == 0:
                    # Supprimer le mapping associé
                    conn.execute("DELETE FROM category_mapping WHERE mps_category_id = ?", (n4_id,))
                    conn.execute("DELETE FROM category WHERE id = ?", (n4_id,))
                    print(f"  Supprimé: {n4_name} (sous {n3_name}, 0 produits)")
                    deleted_total += 1
                else:
                    print(f"  ⚠ Gardé: {n4_name} (sous {n3_name}, {prod_count} produits)")
    
    # Nettoyer sous Vêtements Femme : supprimer N4 avec "Homme" dans le nom
    print(f"\n=== Nettoyage sous Vêtements Femme ===")
    for n3_id, n3_name in femme_n3s:
        n4s = conn.execute(
            "SELECT id, name FROM category WHERE parent_id = ? AND cj_category_id IS NULL", (n3_id,)
        ).fetchall()
        
        for n4_id, n4_name in n4s:
            if 'Homme' in n4_name and 'Femme' not in n4_name:
                prod_count = conn.execute("SELECT COUNT(*) FROM product WHERE category_id = ?", (n4_id,)).fetchone()[0]
                if prod_count == 0:
                    conn.execute("DELETE FROM category_mapping WHERE mps_category_id = ?", (n4_id,))
                    conn.execute("DELETE FROM category WHERE id = ?", (n4_id,))
                    print(f"  Supprimé: {n4_name} (sous {n3_name}, 0 produits)")
                    deleted_total += 1
                else:
                    print(f"  ⚠ Gardé: {n4_name} (sous {n3_name}, {prod_count} produits)")
    
    # Supprimer les catégories MPS vides (0 produits, 0 enfants) sous Mode & Vêtements
    print(f"\n=== Suppression des catégories vides (0 produits, 0 enfants) ===")
    
    def cleanup_empty(parent_id, depth=0):
        nonlocal deleted_total
        children = conn.execute(
            "SELECT id, name, level FROM category WHERE parent_id = ? AND cj_category_id IS NULL ORDER BY name",
            (parent_id,)
        ).fetchall()
        
        for child_id, child_name, child_level in children:
            # D'abord nettoyer les enfants
            cleanup_empty(child_id, depth + 1)
            
            # Vérifier si cette catégorie est vide
            prod_count = conn.execute("SELECT COUNT(*) FROM product WHERE category_id = ?", (child_id,)).fetchone()[0]
            sub_count = conn.execute("SELECT COUNT(*) FROM category WHERE parent_id = ? AND cj_category_id IS NULL", (child_id,)).fetchone()[0]
            
            if prod_count == 0 and sub_count == 0 and child_level >= 4:
                conn.execute("DELETE FROM category_mapping WHERE mps_category_id = ?", (child_id,))
                conn.execute("DELETE FROM category WHERE id = ?", (child_id,))
                prefix = "  " * depth
                print(f"  {prefix}Supprimé N{child_level}: {child_name} (vide)")
                deleted_total += 1
    
    cleanup_empty(52)
    
    conn.commit()
    
    print(f"\n=== {deleted_total} catégories supprimées au total ===")
    
    # Vérification finale
    print(f"\n{'=' * 70}")
    print("STRUCTURE FINALE : Mode & Vêtements")
    print(f"{'=' * 70}")
    
    def print_tree(parent_id, indent=0):
        rows = conn.execute('''
            SELECT c.id, c.name, c.level, 
                   (SELECT COUNT(*) FROM product WHERE category_id = c.id) as prods,
                   (SELECT COUNT(*) FROM category WHERE parent_id = c.id AND cj_category_id IS NULL) as children
            FROM category c
            WHERE c.parent_id = ? AND c.cj_category_id IS NULL
            ORDER BY c.name
        ''', (parent_id,)).fetchall()
        
        for r in rows:
            prefix = "  " * indent
            prod_str = f"{r[3]} prod" if r[3] > 0 else ""
            child_str = f"{r[4]} ss-cat" if r[4] > 0 else ""
            info = ", ".join(filter(None, [child_str, prod_str]))
            print(f"{prefix}N{r[2]} {r[1]} ({info})")
            if r[4] > 0 and indent < 3:
                print_tree(r[0], indent + 1)
    
    print_tree(52)
    
    # Stats globales
    total_mps = conn.execute("SELECT COUNT(*) FROM category WHERE cj_category_id IS NULL").fetchone()[0]
    total_mappings = conn.execute("SELECT COUNT(*) FROM category_mapping").fetchone()[0]
    non_classe = conn.execute("SELECT COUNT(*) FROM product WHERE category_id = (SELECT id FROM category WHERE slug = 'non-classe')").fetchone()[0]
    
    print(f"\nStats globales:")
    print(f"  Catégories MPS: {total_mps}")
    print(f"  Mappings: {total_mappings}")
    print(f"  Produits 'Non classé': {non_classe}")
    
    conn.close()
    print("\nDONE")


if __name__ == '__main__':
    run()
