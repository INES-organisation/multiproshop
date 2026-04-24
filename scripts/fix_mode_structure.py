"""
Corriger la structure Mode & Vêtements :
- Déplacer les catégories N2 mal placées sous le bon parent N2 (Vêtements Homme, Vêtements Femme, Sacs & Chaussures)
- Ajuster les niveaux (N2→N3, N3→N4)
- Supprimer les doublons
"""
import sqlite3, json, os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'multiproshop.db')

# Mapping : catégorie CJ N2 -> parent MPS N2
# Basé sur les CJ N1 parents
CJ_N1_TO_MPS_N2 = {
    "Bags & Shoes": "Sacs & Chaussures",
    "Men's Clothing": "Vêtements Homme",
    "Women's Clothing": "Vêtements Femme",
}

MODE_MPS_ID = 52

def run():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('PRAGMA foreign_keys = OFF')
    
    provider_id = conn.execute("SELECT id FROM api_provider WHERE slug = 'cj-dropshipping'").fetchone()[0]
    
    # Récupérer les IDs des 3 N2 intermédiaires
    mps_n2_ids = {}
    for name in ["Vêtements Homme", "Vêtements Femme", "Sacs & Chaussures"]:
        row = conn.execute(
            "SELECT id FROM category WHERE name = ? AND parent_id = ? AND cj_category_id IS NULL",
            (name, MODE_MPS_ID)
        ).fetchone()
        if row:
            mps_n2_ids[name] = row[0]
            print(f"  {name}: id={row[0]}")
        else:
            print(f"  ERREUR: {name} non trouvé!")
            return
    
    # Récupérer toutes les catégories MPS directement sous Mode & Vêtements (id=52)
    # qui ne sont PAS les 3 N2 intermédiaires
    wrong_n2s = conn.execute('''
        SELECT id, name FROM category 
        WHERE parent_id = ? AND cj_category_id IS NULL 
        AND id NOT IN (?, ?, ?)
        ORDER BY name
    ''', (MODE_MPS_ID, mps_n2_ids["Vêtements Homme"], mps_n2_ids["Vêtements Femme"], mps_n2_ids["Sacs & Chaussures"])).fetchall()
    
    print(f"\n{len(wrong_n2s)} catégories mal placées directement sous Mode & Vêtements:")
    
    # Pour chaque catégorie mal placée, trouver son CJ N2 parent pour déterminer le bon N2 MPS
    moved = 0
    merged = 0
    
    for wrong_id, wrong_name in wrong_n2s:
        # Trouver le mapping CJ associé
        mapping = conn.execute('''
            SELECT cm.external_category_id, c_cj.parent_id
            FROM category_mapping cm
            JOIN category c_cj ON c_cj.cj_category_id = cm.external_category_id
            WHERE cm.mps_category_id = ?
        ''', (wrong_id,)).fetchone()
        
        if not mapping:
            print(f"  {wrong_name} (id={wrong_id}): pas de mapping, skip")
            continue
        
        cj_ext_id, cj_parent_db_id = mapping
        
        # Trouver le CJ N1 parent
        cj_n1 = conn.execute(
            "SELECT name FROM category WHERE id = ? AND cj_category_id IS NOT NULL",
            (cj_parent_db_id,)
        ).fetchone()
        
        if not cj_n1:
            print(f"  {wrong_name} (id={wrong_id}): CJ parent non trouvé, skip")
            continue
        
        cj_n1_name = cj_n1[0]
        target_n2_name = CJ_N1_TO_MPS_N2.get(cj_n1_name)
        
        if not target_n2_name:
            print(f"  {wrong_name} (id={wrong_id}): CJ N1={cj_n1_name} pas dans le mapping, skip")
            continue
        
        target_n2_id = mps_n2_ids[target_n2_name]
        
        # Vérifier si une catégorie avec le même nom existe déjà sous le bon parent
        existing = conn.execute(
            "SELECT id FROM category WHERE parent_id = ? AND name = ? AND cj_category_id IS NULL",
            (target_n2_id, wrong_name)
        ).fetchone()
        
        if existing:
            existing_id = existing[0]
            # Fusionner : déplacer les produits et enfants vers l'existante, supprimer la mal placée
            
            # Déplacer les produits
            conn.execute("UPDATE product SET category_id = ? WHERE category_id = ?", (existing_id, wrong_id))
            
            # Déplacer les enfants
            children = conn.execute(
                "SELECT id, name FROM category WHERE parent_id = ? AND cj_category_id IS NULL", (wrong_id,)
            ).fetchall()
            
            for child_id, child_name in children:
                # Vérifier si un enfant avec le même nom existe déjà sous l'existante
                existing_child = conn.execute(
                    "SELECT id FROM category WHERE parent_id = ? AND name = ? AND cj_category_id IS NULL",
                    (existing_id, child_name)
                ).fetchone()
                
                if existing_child:
                    # Fusionner les produits
                    conn.execute("UPDATE product SET category_id = ? WHERE category_id = ?", (existing_child[0], child_id))
                    # Mettre à jour le mapping
                    conn.execute("UPDATE category_mapping SET mps_category_id = ? WHERE mps_category_id = ?", (existing_child[0], child_id))
                    conn.execute("DELETE FROM category WHERE id = ?", (child_id,))
                else:
                    conn.execute("UPDATE category SET parent_id = ?, level = 4 WHERE id = ?", (existing_id, child_id))
            
            # Mettre à jour le mapping
            conn.execute("UPDATE category_mapping SET mps_category_id = ? WHERE mps_category_id = ?", (existing_id, wrong_id))
            conn.execute("DELETE FROM category WHERE id = ?", (wrong_id,))
            
            print(f"  ✓ {wrong_name}: fusionné avec existant (id={existing_id}) sous {target_n2_name}")
            merged += 1
        else:
            # Déplacer sous le bon parent et ajuster le niveau
            conn.execute("UPDATE category SET parent_id = ?, level = 3 WHERE id = ?", (target_n2_id, wrong_id))
            
            # Ajuster les enfants (N3→N4)
            conn.execute("UPDATE category SET level = 4 WHERE parent_id = ? AND cj_category_id IS NULL", (wrong_id,))
            
            print(f"  ✓ {wrong_name}: déplacé sous {target_n2_name} (N2→N3)")
            moved += 1
    
    conn.commit()
    
    print(f"\n  Déplacés: {moved}, Fusionnés: {merged}")
    
    # Vérification finale
    print(f"\n{'=' * 60}")
    print("STRUCTURE Mode & Vêtements:")
    print(f"{'=' * 60}")
    
    # Vérifier qu'il ne reste que les 3 N2 sous Mode
    n2s = conn.execute(
        "SELECT id, name FROM category WHERE parent_id = ? AND cj_category_id IS NULL ORDER BY name",
        (MODE_MPS_ID,)
    ).fetchall()
    
    for n2_id, n2_name in n2s:
        n3s = conn.execute(
            "SELECT id, name FROM category WHERE parent_id = ? AND cj_category_id IS NULL ORDER BY name",
            (n2_id,)
        ).fetchall()
        print(f"\nN2 {n2_name} ({len(n3s)} sous-catégories)")
        for n3_id, n3_name in n3s:
            n4_count = conn.execute(
                "SELECT COUNT(*) FROM category WHERE parent_id = ? AND cj_category_id IS NULL",
                (n3_id,)
            ).fetchone()[0]
            prod_count = conn.execute(
                "SELECT COUNT(*) FROM product WHERE category_id = ?", (n3_id,)
            ).fetchone()[0]
            print(f"  N3 {n3_name} ({n4_count} N4, {prod_count} prod)")
    
    # Stats
    non_classe = conn.execute("SELECT COUNT(*) FROM product WHERE category_id = (SELECT id FROM category WHERE slug = 'non-classe')").fetchone()[0]
    print(f"\nProduits 'Non classé': {non_classe}")
    
    conn.close()
    print("\nDONE")


if __name__ == '__main__':
    run()
