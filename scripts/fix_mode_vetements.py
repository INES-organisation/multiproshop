"""
Corriger Mode & Vêtements : 
- Les catégories partagées (Accessoires, Bas, Manteaux & Vestes) ont été mises 
  uniquement sous Vêtements Homme. Il faut créer des copies pour Vêtements Femme
  avec les bons mappings CJ.
"""
import sqlite3, json, os
from slugify import slugify

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'multiproshop.db')

def run():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('PRAGMA foreign_keys = OFF')
    
    provider_id = conn.execute("SELECT id FROM api_provider WHERE slug = 'cj-dropshipping'").fetchone()[0]
    existing_slugs = set(r[0] for r in conn.execute("SELECT slug FROM category").fetchall())
    
    # IDs des nouveaux N2 MPS
    VET_HOMME_ID = conn.execute("SELECT id FROM category WHERE name = 'Vêtements Homme' AND parent_id = 52").fetchone()[0]
    VET_FEMME_ID = conn.execute("SELECT id FROM category WHERE name = 'Vêtements Femme' AND parent_id = 52").fetchone()[0]
    
    print(f"Vêtements Homme: id={VET_HOMME_ID}")
    print(f"Vêtements Femme: id={VET_FEMME_ID}")
    
    # CJ N1 Women's Clothing
    cj_women_id = conn.execute("SELECT id FROM category WHERE name = 'Women''s Clothing' AND cj_category_id IS NOT NULL AND level = 1").fetchone()[0]
    print(f"CJ Women's Clothing: db_id={cj_women_id}")
    
    # Récupérer les CJ N2 de Women's Clothing
    cj_women_n2 = conn.execute('''
        SELECT id, cj_category_id, name, name_fr
        FROM category
        WHERE parent_id = ? AND cj_category_id IS NOT NULL
        ORDER BY name
    ''', (cj_women_id,)).fetchall()
    
    print(f"\n{len(cj_women_n2)} CJ N2 sous Women's Clothing:")
    
    for cj_n2_db_id, cj_n2_cj_id, cj_n2_name, cj_n2_name_fr in cj_women_n2:
        mps_name = cj_n2_name_fr or cj_n2_name
        
        # Vérifier le mapping actuel
        current = conn.execute('''
            SELECT cm.mps_category_id, c.name, c.parent_id
            FROM category_mapping cm
            JOIN category c ON c.id = cm.mps_category_id
            WHERE cm.external_category_id = ?
        ''', (cj_n2_cj_id,)).fetchone()
        
        if current and current[2] == VET_FEMME_ID:
            print(f"  ✓ {mps_name}: déjà sous Vêtements Femme")
            continue
        
        if current and current[2] == VET_HOMME_ID:
            # Cette catégorie est sous Vêtements Homme mais devrait avoir une copie Femme
            print(f"  ✗ {mps_name}: sous Vêtements Homme, création copie Femme...")
            
            # Créer une nouvelle catégorie MPS N3 sous Vêtements Femme
            # Ajouter "Femme" au nom pour différencier
            mps_name_femme = f"{mps_name} Femme"
            mps_slug = slugify(f"mode-vetements-femme-{mps_name}")
            
            base_slug = mps_slug
            counter = 1
            while mps_slug in existing_slugs:
                mps_slug = f"{base_slug}-{counter}"
                counter += 1
            existing_slugs.add(mps_slug)
            
            max_order = conn.execute(
                "SELECT COALESCE(MAX([order]), 0) FROM category WHERE parent_id = ?",
                (VET_FEMME_ID,)
            ).fetchone()[0] + 1
            
            conn.execute('''
                INSERT INTO category (name, name_fr, slug, level, parent_id, [order], is_active, visible, product_count)
                VALUES (?, ?, ?, 3, ?, ?, 1, 1, 0)
            ''', (mps_name_femme, mps_name_femme, mps_slug, VET_FEMME_ID, max_order))
            new_mps_n3_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            
            # Renommer l'existante sous Homme pour clarifier
            old_mps_id = current[0]
            old_name = current[1]
            if not old_name.endswith(' Homme'):
                new_name_homme = f"{old_name} Homme"
                conn.execute("UPDATE category SET name = ?, name_fr = ? WHERE id = ?", 
                           (new_name_homme, new_name_homme, old_mps_id))
                print(f"    Renommé: {old_name} -> {new_name_homme} (sous Vêtements Homme)")
            
            # Mettre à jour le mapping CJ N2 Women -> nouvelle MPS N3 Femme
            conn.execute('''
                UPDATE category_mapping SET mps_category_id = ? WHERE external_category_id = ? AND provider_id = ?
            ''', (new_mps_n3_id, cj_n2_cj_id, provider_id))
            
            print(f"    Créé: {mps_name_femme} (id={new_mps_n3_id}) sous Vêtements Femme")
            
            # Créer les sous-catégories N4 pour Femme (copie des CJ N3)
            cj_n3_children = conn.execute('''
                SELECT id, cj_category_id, name, name_fr
                FROM category
                WHERE parent_id = ? AND cj_category_id IS NOT NULL
                ORDER BY name
            ''', (cj_n2_db_id,)).fetchall()
            
            for cj_n3_db_id, cj_n3_cj_id, cj_n3_name, cj_n3_name_fr in cj_n3_children:
                n4_name = cj_n3_name_fr or cj_n3_name
                n4_slug = slugify(f"{mps_slug}-{n4_name}")
                
                base_slug = n4_slug
                counter = 1
                while n4_slug in existing_slugs:
                    n4_slug = f"{base_slug}-{counter}"
                    counter += 1
                existing_slugs.add(n4_slug)
                
                conn.execute('''
                    INSERT INTO category (name, name_fr, slug, level, parent_id, [order], is_active, visible, product_count)
                    VALUES (?, ?, ?, 4, ?, 0, 1, 1, 0)
                ''', (n4_name, n4_name, n4_slug, new_mps_n3_id))
                new_n4_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
                
                # Mettre à jour le mapping CJ N3 -> nouvelle MPS N4
                conn.execute('''
                    UPDATE category_mapping SET mps_category_id = ? WHERE external_category_id = ? AND provider_id = ?
                ''', (new_n4_id, cj_n3_cj_id, provider_id))
            
            print(f"    + {len(cj_n3_children)} sous-catégories N4 créées")
        
        elif not current:
            print(f"  ? {mps_name}: pas de mapping, création sous Vêtements Femme...")
            # Créer la catégorie et le mapping
            mps_slug = slugify(f"mode-vetements-femme-{mps_name}")
            base_slug = mps_slug
            counter = 1
            while mps_slug in existing_slugs:
                mps_slug = f"{base_slug}-{counter}"
                counter += 1
            existing_slugs.add(mps_slug)
            
            max_order = conn.execute(
                "SELECT COALESCE(MAX([order]), 0) FROM category WHERE parent_id = ?",
                (VET_FEMME_ID,)
            ).fetchone()[0] + 1
            
            conn.execute('''
                INSERT INTO category (name, name_fr, slug, level, parent_id, [order], is_active, visible, product_count)
                VALUES (?, ?, ?, 3, ?, ?, 1, 1, 0)
            ''', (mps_name, mps_name, mps_slug, VET_FEMME_ID, max_order))
            new_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            
            conn.execute('''
                INSERT INTO category_mapping (provider_id, external_category_id, external_category_name, mps_category_id, auto_import, apply_markup)
                VALUES (?, ?, ?, ?, 1, 1.3)
            ''', (provider_id, cj_n2_cj_id, cj_n2_name, new_id))
            
            print(f"    Créé: {mps_name} (id={new_id})")
    
    conn.commit()
    
    # Réassigner les produits
    print(f"\n{'=' * 70}")
    print("RÉASSIGNATION DES PRODUITS...")
    
    all_mappings = conn.execute(
        'SELECT external_category_id, mps_category_id FROM category_mapping WHERE provider_id = ?',
        (provider_id,)
    ).fetchall()
    cj_to_mps = {ext_id: mps_id for ext_id, mps_id in all_mappings}
    
    products = conn.execute('SELECT id, cj_raw_data, category_id FROM product WHERE cj_raw_data IS NOT NULL').fetchall()
    moved = 0
    for pid, raw_json, current_cat_id in products:
        try:
            raw = json.loads(raw_json)
            product_cj_cat_id = raw.get('categoryId') or raw.get('category_id') or ''
            if product_cj_cat_id and product_cj_cat_id in cj_to_mps:
                target = cj_to_mps[product_cj_cat_id]
                if current_cat_id != target:
                    conn.execute('UPDATE product SET category_id = ? WHERE id = ?', (target, pid))
                    moved += 1
        except:
            pass
    
    conn.commit()
    print(f"  {moved} produits réassignés")
    
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
            print(f"{prefix}N{r[2]} {r[1]} ({r[4]} enfants, {r[3]} produits)")
            if r[4] > 0 and indent < 3:
                print_tree(r[0], indent + 1)
    
    print_tree(52)
    
    conn.close()
    print("\nDONE")


if __name__ == '__main__':
    run()
