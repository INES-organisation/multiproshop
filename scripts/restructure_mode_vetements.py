"""
Restructurer Mode & Vêtements (id=52) :
- Créer 3 sous-catégories N2 : "Vêtements Homme", "Vêtements Femme", "Sacs & Chaussures"
- Déplacer les sous-catégories MPS actuelles (N2→N3, N3→N4) sous le bon parent
- Mettre à jour les mappings et réassigner les produits
"""
import sqlite3, json, os
from slugify import slugify

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'multiproshop.db')

# Mapping CJ N1 -> nouveau nom MPS N2
CJ_TO_MPS_N2 = {
    "Men's Clothing": "Vêtements Homme",
    "Women's Clothing": "Vêtements Femme",
    "Bags & Shoes": "Sacs & Chaussures",
}

MODE_MPS_ID = 52  # Mode & Vêtements


def run():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('PRAGMA foreign_keys = OFF')
    
    print("=" * 70)
    print("RESTRUCTURATION : Mode & Vêtements")
    print("=" * 70)
    
    provider_id = conn.execute("SELECT id FROM api_provider WHERE slug = 'cj-dropshipping'").fetchone()[0]
    
    # Récupérer les CJ N1 mappées vers Mode & Vêtements
    cj_n1_rows = conn.execute('''
        SELECT c.id, c.name, c.cj_category_id
        FROM category c
        JOIN category_mapping cm ON cm.external_category_id = c.cj_category_id
        WHERE cm.mps_category_id = ? AND c.level = 1
    ''', (MODE_MPS_ID,)).fetchall()
    
    print(f"\n{len(cj_n1_rows)} CJ N1 mappées vers Mode & Vêtements:")
    for r in cj_n1_rows:
        print(f"  {r[1]} (cj_db_id={r[0]})")
    
    # Récupérer les slugs existants pour éviter les doublons
    existing_slugs = set(r[0] for r in conn.execute("SELECT slug FROM category").fetchall())
    
    for cj_db_id, cj_name, cj_cj_id in cj_n1_rows:
        mps_n2_name = CJ_TO_MPS_N2.get(cj_name)
        if not mps_n2_name:
            print(f"\n  SKIP: {cj_name} (pas dans CJ_TO_MPS_N2)")
            continue
        
        print(f"\n{'─' * 60}")
        print(f"  CJ N1: {cj_name} -> Nouveau MPS N2: {mps_n2_name}")
        
        # Vérifier si le MPS N2 existe déjà
        mps_n2_slug = slugify(f"mode-vetements-{mps_n2_name}")
        existing = conn.execute(
            "SELECT id FROM category WHERE parent_id = ? AND cj_category_id IS NULL AND name = ?",
            (MODE_MPS_ID, mps_n2_name)
        ).fetchone()
        
        if existing:
            mps_n2_id = existing[0]
            print(f"    MPS N2 existe déjà (id={mps_n2_id})")
        else:
            # Assurer unicité du slug
            base_slug = mps_n2_slug
            counter = 1
            while mps_n2_slug in existing_slugs:
                mps_n2_slug = f"{base_slug}-{counter}"
                counter += 1
            existing_slugs.add(mps_n2_slug)
            
            conn.execute('''
                INSERT INTO category (name, name_fr, slug, level, parent_id, [order], is_active, visible, product_count)
                VALUES (?, ?, ?, 2, ?, 0, 1, 1, 0)
            ''', (mps_n2_name, mps_n2_name, mps_n2_slug, MODE_MPS_ID))
            mps_n2_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            print(f"    MPS N2 créé: {mps_n2_name} (id={mps_n2_id})")
        
        # Récupérer les CJ N2 enfants de ce CJ N1
        cj_n2_children = conn.execute('''
            SELECT id, cj_category_id, name, name_fr
            FROM category
            WHERE parent_id = ? AND cj_category_id IS NOT NULL
            ORDER BY name
        ''', (cj_db_id,)).fetchall()
        
        print(f"    {len(cj_n2_children)} CJ N2 à traiter")
        
        for cj_n2_db_id, cj_n2_cj_id, cj_n2_name, cj_n2_name_fr in cj_n2_children:
            mps_n3_name = cj_n2_name_fr or cj_n2_name
            
            # Trouver la sous-catégorie MPS actuelle (N2 sous Mode) qui correspond
            # Elle a été créée par le script précédent directement sous Mode (id=52)
            current_mps = conn.execute('''
                SELECT cm.mps_category_id, c.name, c.parent_id, c.level
                FROM category_mapping cm
                JOIN category c ON c.id = cm.mps_category_id
                WHERE cm.external_category_id = ? AND cm.provider_id = ?
            ''', (cj_n2_cj_id, provider_id)).fetchone()
            
            if current_mps:
                current_mps_id, current_mps_name, current_parent, current_level = current_mps
                
                if current_parent == MODE_MPS_ID:
                    # Déplacer cette catégorie MPS sous le nouveau N2
                    conn.execute('''
                        UPDATE category SET parent_id = ?, level = 3 WHERE id = ?
                    ''', (mps_n2_id, current_mps_id))
                    
                    # Mettre à jour les enfants (N3 -> N4)
                    conn.execute('''
                        UPDATE category SET level = 4 WHERE parent_id = ? AND cj_category_id IS NULL
                    ''', (current_mps_id,))
                    
                    n4_count = conn.execute(
                        "SELECT changes()"
                    ).fetchone()[0]
                    
                    print(f"      {current_mps_name}: N2→N3 (parent={mps_n2_id}) + {n4_count} enfants N3→N4")
                elif current_parent == mps_n2_id:
                    print(f"      {current_mps_name}: déjà sous {mps_n2_name}")
                else:
                    print(f"      {current_mps_name}: parent={current_parent} (inattendu)")
            else:
                print(f"      {mps_n3_name}: pas de mapping trouvé pour {cj_n2_cj_id}")
    
    conn.commit()
    
    # Vérification
    print(f"\n{'=' * 70}")
    print("VÉRIFICATION")
    print(f"{'=' * 70}")
    
    # Afficher la structure Mode & Vêtements
    n2s = conn.execute('''
        SELECT id, name, level FROM category 
        WHERE parent_id = ? AND cj_category_id IS NULL 
        ORDER BY name
    ''', (MODE_MPS_ID,)).fetchall()
    
    print(f"\nMode & Vêtements (id={MODE_MPS_ID}):")
    for n2_id, n2_name, n2_level in n2s:
        n3s = conn.execute('''
            SELECT id, name FROM category 
            WHERE parent_id = ? AND cj_category_id IS NULL 
            ORDER BY name
        ''', (n2_id,)).fetchall()
        
        prod_count = conn.execute(
            "SELECT COUNT(*) FROM product WHERE category_id = ?", (n2_id,)
        ).fetchone()[0]
        
        print(f"  N{n2_level} {n2_name} ({len(n3s)} enfants, {prod_count} produits directs)")
        
        for n3_id, n3_name in n3s[:5]:
            n4s = conn.execute(
                "SELECT COUNT(*) FROM category WHERE parent_id = ? AND cj_category_id IS NULL",
                (n3_id,)
            ).fetchall()
            n4_count = n4s[0][0] if n4s else 0
            
            n3_prods = conn.execute(
                "SELECT COUNT(*) FROM product WHERE category_id = ?", (n3_id,)
            ).fetchone()[0]
            
            print(f"    N3 {n3_name} ({n4_count} N4, {n3_prods} produits)")
        
        if len(n3s) > 5:
            print(f"    ... et {len(n3s) - 5} autres")
    
    conn.close()
    print("\nDONE")


if __name__ == '__main__':
    run()
