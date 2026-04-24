"""Diagnostic approfondi : comprendre pourquoi les produits ne matchent pas"""
import sqlite3, json, os
from collections import Counter

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'multiproshop.db')
conn = sqlite3.connect(DB_PATH)

# 1. Analyser les categoryId dans cj_raw_data
print("=== Analyse des categoryId dans cj_raw_data ===")
products = conn.execute('SELECT id, cj_raw_data, category_id FROM product WHERE cj_raw_data IS NOT NULL').fetchall()

cat_id_counter = Counter()
cat_name_counter = Counter()
missing_cat_ids = set()

for pid, raw_json, current_cat_id in products:
    try:
        raw = json.loads(raw_json)
        cj_cat_id = raw.get('categoryId', '')
        cj_cat_name = raw.get('categoryName', '')
        cat_id_counter[cj_cat_id] += 1
        cat_name_counter[cj_cat_name] += 1
    except:
        pass

print(f"Total produits: {len(products)}")
print(f"categoryId distincts dans cj_raw_data: {len(cat_id_counter)}")

# 2. Vérifier combien de ces categoryId existent dans la table category
all_cj_ids = set(conn.execute('SELECT cj_category_id FROM category WHERE cj_category_id IS NOT NULL').fetchall())
all_cj_ids = set([r[0] for r in conn.execute('SELECT cj_category_id FROM category WHERE cj_category_id IS NOT NULL').fetchall()])

found = 0
not_found = 0
not_found_details = Counter()
for cj_id, count in cat_id_counter.items():
    if cj_id in all_cj_ids:
        found += count
    else:
        not_found += count
        not_found_details[cj_id] = count

print(f"\nProduits avec categoryId trouvé en base: {found}")
print(f"Produits avec categoryId NON trouvé en base: {not_found}")

if not_found_details:
    print(f"\ncategoryId manquants (top 20):")
    for cj_id, count in not_found_details.most_common(20):
        # Chercher le categoryName correspondant
        for pid, raw_json, _ in products:
            try:
                raw = json.loads(raw_json)
                if raw.get('categoryId') == cj_id:
                    print(f"  {cj_id} -> {raw.get('categoryName','')} ({count} produits)")
                    break
            except:
                pass

# 3. Pour les 3 mappings existants, détailler
print("\n=== Détail par mapping ===")
mappings = conn.execute('SELECT external_category_id, external_category_name, mps_category_id FROM category_mapping').fetchall()

for ext_id, ext_name, mps_id in mappings:
    cat = conn.execute('SELECT id, level FROM category WHERE cj_category_id = ?', (ext_id,)).fetchone()
    if not cat:
        continue
    cat_db_id, cat_level = cat
    
    # Collecter CJ IDs (cette cat + enfants + petits-enfants)
    cj_ids = set([ext_id])
    children = conn.execute('SELECT id, cj_category_id FROM category WHERE parent_id = ? AND cj_category_id IS NOT NULL', (cat_db_id,)).fetchall()
    for child_id, child_cj_id in children:
        cj_ids.add(child_cj_id)
        gcs = conn.execute('SELECT cj_category_id FROM category WHERE parent_id = ? AND cj_category_id IS NOT NULL', (child_id,)).fetchall()
        for gc in gcs:
            cj_ids.add(gc[0])
    
    # Compter produits matchant
    matched = 0
    for pid, raw_json, _ in products:
        try:
            raw = json.loads(raw_json)
            if raw.get('categoryId', '') in cj_ids:
                matched += 1
        except:
            pass
    
    # Compter produits dont categoryName commence par ext_name
    name_matched = 0
    for pid, raw_json, _ in products:
        try:
            raw = json.loads(raw_json)
            cn = raw.get('categoryName', '')
            if cn and cn.startswith(ext_name):
                name_matched += 1
        except:
            pass
    
    in_mps = conn.execute('SELECT COUNT(*) FROM product WHERE category_id = ?', (mps_id,)).fetchone()[0]
    print(f"\n  {ext_name} (N{cat_level}):")
    print(f"    CJ IDs collectés: {len(cj_ids)}")
    print(f"    Match par categoryId: {matched}")
    print(f"    Match par categoryName startswith: {name_matched}")
    print(f"    Actuellement dans MPS: {in_mps}")

conn.close()
