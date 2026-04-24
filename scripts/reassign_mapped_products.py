"""Réassigner les produits pour tous les mappings existants (corrige le bug des 2 formats)"""
import sqlite3, json, os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'multiproshop.db')
conn = sqlite3.connect(DB_PATH)

# Récupérer tous les mappings
mappings = conn.execute('SELECT external_category_id, external_category_name, mps_category_id FROM category_mapping').fetchall()
print(f"=== {len(mappings)} mappings à traiter ===\n")

# Charger tous les cj_category_id existants
all_cj_ids = set(r[0] for r in conn.execute('SELECT cj_category_id FROM category WHERE cj_category_id IS NOT NULL').fetchall())

# Charger tous les produits une seule fois
products = conn.execute('SELECT id, cj_raw_data, category_id FROM product WHERE cj_raw_data IS NOT NULL').fetchall()
print(f"Total produits à scanner: {len(products)}\n")

total_moved = 0

for ext_id, ext_name, mps_id in mappings:
    # Trouver la catégorie CJ
    cat = conn.execute('SELECT id, level FROM category WHERE cj_category_id = ?', (ext_id,)).fetchone()
    if not cat:
        print(f"  ERREUR: catégorie CJ {ext_id} non trouvée")
        continue
    
    cat_db_id, cat_level = cat
    
    # Collecter tous les cj_category_id (cette cat + enfants + petits-enfants)
    cj_ids = set([ext_id])
    children = conn.execute('SELECT id, cj_category_id FROM category WHERE parent_id = ? AND cj_category_id IS NOT NULL', (cat_db_id,)).fetchall()
    for child_id, child_cj_id in children:
        cj_ids.add(child_cj_id)
        gcs = conn.execute('SELECT cj_category_id FROM category WHERE parent_id = ? AND cj_category_id IS NOT NULL', (child_id,)).fetchall()
        for gc in gcs:
            cj_ids.add(gc[0])
    
    # Réassigner les produits
    moved = 0
    for pid, raw_json, current_cat_id in products:
        try:
            raw = json.loads(raw_json)
            # Supporter les 2 formats
            product_cj_cat_id = raw.get('categoryId') or raw.get('category_id') or ''
            if product_cj_cat_id in cj_ids and current_cat_id != mps_id:
                conn.execute('UPDATE product SET category_id = ? WHERE id = ?', (mps_id, pid))
                moved += 1
        except:
            pass
    
    mps_name = conn.execute('SELECT name FROM category WHERE id = ?', (mps_id,)).fetchone()[0]
    print(f"  {ext_name} (N{cat_level}, {len(cj_ids)} sous-cat CJ) -> {mps_name}: {moved} produits réassignés")
    total_moved += moved

conn.commit()

# Vérification finale
print(f"\n=== TOTAL: {total_moved} produits réassignés ===\n")
print("Répartition actuelle:")
rows = conn.execute('''
    SELECT c.id, c.name, c.cj_category_id IS NOT NULL as is_cj, COUNT(p.id) as cnt 
    FROM category c 
    LEFT JOIN product p ON p.category_id = c.id 
    GROUP BY c.id 
    HAVING cnt > 0 
    ORDER BY cnt DESC
''').fetchall()
for r in rows:
    tag = "CJ" if r[2] else "MPS"
    print(f"  [{tag}] id={r[0]:5d} | {r[3]:6d} produits | {r[1]}")

conn.close()
print("\nDONE")
