"""
Script pour créer automatiquement les sous-catégories MPS N2/N3 
à partir des catégories CJ N2/N3 (nom français) et les mapper.
Puis réassigner les produits vers les sous-catégories MPS.
"""
import sqlite3, json, os
from slugify import slugify

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'multiproshop.db')

def run():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('PRAGMA foreign_keys = OFF')
    
    print("=" * 70)
    print("CRÉATION DES SOUS-CATÉGORIES MPS + MAPPING AUTOMATIQUE")
    print("=" * 70)
    
    # 1. Récupérer tous les mappings CJ N1 -> MPS N1
    mappings_n1 = conn.execute('''
        SELECT cm.external_category_id, cm.external_category_name, cm.mps_category_id, 
               c_cj.id as cj_db_id, c_cj.level as cj_level,
               c_mps.name as mps_name, c_mps.id as mps_id
        FROM category_mapping cm
        JOIN category c_cj ON c_cj.cj_category_id = cm.external_category_id
        JOIN category c_mps ON c_mps.id = cm.mps_category_id
        WHERE c_cj.level = 1
        ORDER BY c_mps.name
    ''').fetchall()
    
    print(f"\n{len(mappings_n1)} mappings CJ N1 -> MPS N1 trouvés")
    
    # Récupérer le provider CJ
    provider = conn.execute("SELECT id FROM api_provider WHERE slug = 'cj-dropshipping'").fetchone()
    if not provider:
        print("ERREUR: Provider CJ non trouvé")
        return
    provider_id = provider[0]
    
    # Récupérer les sous-catégories MPS déjà existantes (pour ne pas les recréer)
    existing_mps_slugs = set(r[0] for r in conn.execute(
        "SELECT slug FROM category WHERE cj_category_id IS NULL"
    ).fetchall())
    
    # Récupérer les mappings déjà existants
    existing_mappings = set(r[0] for r in conn.execute(
        "SELECT external_category_id FROM category_mapping WHERE provider_id = ?", (provider_id,)
    ).fetchall())
    
    total_created_n2 = 0
    total_created_n3 = 0
    total_mapped = 0
    
    for ext_id, ext_name, mps_id, cj_db_id, cj_level, mps_name, mps_db_id in mappings_n1:
        print(f"\n{'─' * 60}")
        print(f"  CJ N1: {ext_name} -> MPS N1: {mps_name} (id={mps_db_id})")
        
        # Récupérer les enfants CJ N2
        cj_n2_children = conn.execute('''
            SELECT id, cj_category_id, name, name_fr, level 
            FROM category 
            WHERE parent_id = ? AND cj_category_id IS NOT NULL
            ORDER BY name
        ''', (cj_db_id,)).fetchall()
        
        if not cj_n2_children:
            print(f"    Pas de sous-catégories CJ N2")
            continue
        
        print(f"    {len(cj_n2_children)} sous-catégories CJ N2")
        
        # Récupérer le prochain order pour les sous-catégories MPS N2
        max_order = conn.execute(
            "SELECT COALESCE(MAX([order]), 0) FROM category WHERE parent_id = ? AND cj_category_id IS NULL",
            (mps_db_id,)
        ).fetchone()[0]
        
        for cj_n2_id, cj_n2_cj_id, cj_n2_name, cj_n2_name_fr, cj_n2_level in cj_n2_children:
            # Nom français pour la sous-catégorie MPS
            mps_n2_name = cj_n2_name_fr or cj_n2_name
            mps_n2_slug = slugify(f"{slugify(mps_name)}-{mps_n2_name}")
            
            # Vérifier si cette sous-catégorie MPS existe déjà
            existing_mps_n2 = conn.execute(
                "SELECT id FROM category WHERE parent_id = ? AND cj_category_id IS NULL AND (name = ? OR slug = ?)",
                (mps_db_id, mps_n2_name, mps_n2_slug)
            ).fetchone()
            
            if existing_mps_n2:
                mps_n2_id = existing_mps_n2[0]
            else:
                # Assurer l'unicité du slug
                base_slug = mps_n2_slug
                counter = 1
                while mps_n2_slug in existing_mps_slugs:
                    mps_n2_slug = f"{base_slug}-{counter}"
                    counter += 1
                existing_mps_slugs.add(mps_n2_slug)
                
                max_order += 1
                conn.execute('''
                    INSERT INTO category (name, name_fr, slug, level, parent_id, [order], is_active, visible, product_count)
                    VALUES (?, ?, ?, 2, ?, ?, 1, 1, 0)
                ''', (mps_n2_name, mps_n2_name, mps_n2_slug, mps_db_id, max_order))
                mps_n2_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
                total_created_n2 += 1
            
            # Créer le mapping CJ N2 -> MPS N2 (si pas déjà existant)
            if cj_n2_cj_id not in existing_mappings:
                conn.execute('''
                    INSERT INTO category_mapping (provider_id, external_category_id, external_category_name, mps_category_id, auto_import, apply_markup)
                    VALUES (?, ?, ?, ?, 1, 1.3)
                ''', (provider_id, cj_n2_cj_id, cj_n2_name, mps_n2_id))
                existing_mappings.add(cj_n2_cj_id)
                total_mapped += 1
            
            # Récupérer les enfants CJ N3
            cj_n3_children = conn.execute('''
                SELECT id, cj_category_id, name, name_fr, level 
                FROM category 
                WHERE parent_id = ? AND cj_category_id IS NOT NULL
                ORDER BY name
            ''', (cj_n2_id,)).fetchall()
            
            # Prochain order pour N3
            max_order_n3 = conn.execute(
                "SELECT COALESCE(MAX([order]), 0) FROM category WHERE parent_id = ? AND cj_category_id IS NULL",
                (mps_n2_id,)
            ).fetchone()[0]
            
            for cj_n3_id, cj_n3_cj_id, cj_n3_name, cj_n3_name_fr, cj_n3_level in cj_n3_children:
                mps_n3_name = cj_n3_name_fr or cj_n3_name
                mps_n3_slug = slugify(f"{mps_n2_slug}-{mps_n3_name}")
                
                # Vérifier si cette sous-catégorie MPS N3 existe déjà
                existing_mps_n3 = conn.execute(
                    "SELECT id FROM category WHERE parent_id = ? AND cj_category_id IS NULL AND (name = ? OR slug = ?)",
                    (mps_n2_id, mps_n3_name, mps_n3_slug)
                ).fetchone()
                
                if existing_mps_n3:
                    mps_n3_id = existing_mps_n3[0]
                else:
                    base_slug = mps_n3_slug
                    counter = 1
                    while mps_n3_slug in existing_mps_slugs:
                        mps_n3_slug = f"{base_slug}-{counter}"
                        counter += 1
                    existing_mps_slugs.add(mps_n3_slug)
                    
                    max_order_n3 += 1
                    conn.execute('''
                        INSERT INTO category (name, name_fr, slug, level, parent_id, [order], is_active, visible, product_count)
                        VALUES (?, ?, ?, 3, ?, ?, 1, 1, 0)
                    ''', (mps_n3_name, mps_n3_name, mps_n3_slug, mps_n2_id, max_order_n3))
                    mps_n3_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
                    total_created_n3 += 1
                
                # Créer le mapping CJ N3 -> MPS N3
                if cj_n3_cj_id not in existing_mappings:
                    conn.execute('''
                        INSERT INTO category_mapping (provider_id, external_category_id, external_category_name, mps_category_id, auto_import, apply_markup)
                        VALUES (?, ?, ?, ?, 1, 1.3)
                    ''', (provider_id, cj_n3_cj_id, cj_n3_name, mps_n3_id))
                    existing_mappings.add(cj_n3_cj_id)
                    total_mapped += 1
            
            print(f"    N2: {mps_n2_name} (id={mps_n2_id}) + {len(cj_n3_children)} N3")
    
    conn.commit()
    
    print(f"\n{'=' * 70}")
    print(f"ÉTAPE 1 - CRÉATION TERMINÉE")
    print(f"  Sous-catégories MPS N2 créées: {total_created_n2}")
    print(f"  Sous-catégories MPS N3 créées: {total_created_n3}")
    print(f"  Mappings créés: {total_mapped}")
    print(f"{'=' * 70}")
    
    # ÉTAPE 2 : Réassigner les produits
    print(f"\nÉTAPE 2 - RÉASSIGNATION DES PRODUITS...")
    
    # Charger tous les mappings (y compris les nouveaux)
    all_mappings = conn.execute(
        'SELECT external_category_id, mps_category_id FROM category_mapping WHERE provider_id = ?',
        (provider_id,)
    ).fetchall()
    
    # Créer un dict cj_category_id -> mps_category_id
    cj_to_mps = {}
    for ext_id, mps_id in all_mappings:
        cj_to_mps[ext_id] = mps_id
    
    # Scanner tous les produits et réassigner
    products = conn.execute('SELECT id, cj_raw_data, category_id FROM product WHERE cj_raw_data IS NOT NULL').fetchall()
    
    moved = 0
    for pid, raw_json, current_cat_id in products:
        try:
            raw = json.loads(raw_json)
            product_cj_cat_id = raw.get('categoryId') or raw.get('category_id') or ''
            if product_cj_cat_id and product_cj_cat_id in cj_to_mps:
                target_mps_id = cj_to_mps[product_cj_cat_id]
                if current_cat_id != target_mps_id:
                    conn.execute('UPDATE product SET category_id = ? WHERE id = ?', (target_mps_id, pid))
                    moved += 1
        except:
            pass
    
    conn.commit()
    
    print(f"  {moved} produits réassignés vers les sous-catégories MPS")
    
    # Vérification finale
    print(f"\n{'=' * 70}")
    print("VÉRIFICATION FINALE")
    print(f"{'=' * 70}")
    
    mps_n1 = conn.execute("SELECT COUNT(*) FROM category WHERE cj_category_id IS NULL AND level = 1").fetchone()[0]
    mps_n2 = conn.execute("SELECT COUNT(*) FROM category WHERE cj_category_id IS NULL AND level = 2").fetchone()[0]
    mps_n3 = conn.execute("SELECT COUNT(*) FROM category WHERE cj_category_id IS NULL AND level = 3").fetchone()[0]
    total_mappings = conn.execute("SELECT COUNT(*) FROM category_mapping").fetchone()[0]
    non_classe = conn.execute("SELECT COUNT(*) FROM product WHERE category_id = (SELECT id FROM category WHERE slug = 'non-classe')").fetchone()[0]
    
    print(f"  Catégories MPS: N1={mps_n1}, N2={mps_n2}, N3={mps_n3}")
    print(f"  Total mappings: {total_mappings}")
    print(f"  Produits dans 'Non classé': {non_classe}")
    
    # Top 10 catégories MPS par nombre de produits
    print(f"\n  Top 15 catégories MPS par produits:")
    rows = conn.execute('''
        SELECT c.name, c.level, COUNT(p.id) as cnt
        FROM category c
        JOIN product p ON p.category_id = c.id
        WHERE c.cj_category_id IS NULL
        GROUP BY c.id
        ORDER BY cnt DESC
        LIMIT 15
    ''').fetchall()
    for r in rows:
        print(f"    N{r[1]} {r[0]:45s} {r[2]:6d} produits")
    
    conn.close()
    print("\nDONE")


if __name__ == '__main__':
    run()
