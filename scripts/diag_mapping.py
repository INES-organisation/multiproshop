"""Diagnostic : vérifier pourquoi les produits ne sont pas tous réassignés"""
import sqlite3, json, os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'multiproshop.db')
conn = sqlite3.connect(DB_PATH)

# 1. Mappings actuels
mappings = conn.execute('SELECT external_category_id, external_category_name, mps_category_id FROM category_mapping').fetchall()
print(f"=== {len(mappings)} mappings actuels ===")

for ext_id, ext_name, mps_id in mappings:
    # Trouver la catégorie CJ parente
    cat = conn.execute('SELECT id, name, level FROM category WHERE cj_category_id = ?', (ext_id,)).fetchone()
    if not cat:
        print(f"  ERREUR: catégorie CJ {ext_id} non trouvée")
        continue
    
    cat_db_id, cat_name, cat_level = cat
    
    # Collecter tous les cj_category_id (cette cat + enfants + petits-enfants)
    cj_ids = set([ext_id])
    children = conn.execute('SELECT id, cj_category_id FROM category WHERE parent_id = ? AND cj_category_id IS NOT NULL', (cat_db_id,)).fetchall()
    for child_id, child_cj_id in children:
        cj_ids.add(child_cj_id)
        grandchildren = conn.execute('SELECT cj_category_id FROM category WHERE parent_id = ? AND cj_category_id IS NOT NULL', (child_id,)).fetchall()
        for gc in grandchildren:
            cj_ids.add(gc[0])
    
    print(f"\n  {cat_name} (N{cat_level}) -> MPS id={mps_id}")
    print(f"    cj_category_ids collectés: {len(cj_ids)}")
    
    # Compter les produits qui matchent
    products = conn.execute('SELECT cj_raw_data FROM product WHERE cj_raw_data IS NOT NULL').fetchall()
    matched = 0
    for p in products:
        try:
            raw = json.loads(p[0])
            if raw.get('categoryId', '') in cj_ids:
                matched += 1
        except:
            pass
    
    # Produits actuellement dans la catégorie MPS
    in_mps = conn.execute('SELECT COUNT(*) FROM product WHERE category_id = ?', (mps_id,)).fetchone()[0]
    
    print(f"    Produits matchant categoryId: {matched}")
    print(f"    Produits actuellement dans MPS {mps_id}: {in_mps}")
    if matched != in_mps:
        print(f"    *** ÉCART: {matched - in_mps} produits manquants ***")

# 2. Vérifier les produits dans "Non classé"
non_classe = conn.execute("SELECT id FROM category WHERE slug = 'non-classe'").fetchone()
if non_classe:
    nc_count = conn.execute('SELECT COUNT(*) FROM product WHERE category_id = ?', (non_classe[0],)).fetchone()[0]
    print(f"\n=== Produits dans 'Non classé': {nc_count} ===")

# 3. Vérifier les catégories MPS dans le sélecteur (combien sont CJ vs MPS)
all_cats = conn.execute('SELECT COUNT(*) FROM category').fetchone()[0]
cj_cats = conn.execute('SELECT COUNT(*) FROM category WHERE cj_category_id IS NOT NULL').fetchone()[0]
mps_cats = conn.execute('SELECT COUNT(*) FROM category WHERE cj_category_id IS NULL').fetchone()[0]
print(f"\n=== Catégories dans le sélecteur ===")
print(f"  Total: {all_cats} (CJ: {cj_cats}, MPS: {mps_cats})")
print(f"  Le sélecteur devrait n'afficher que les {mps_cats} MPS")

conn.close()
