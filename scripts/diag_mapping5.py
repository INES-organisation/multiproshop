"""Diagnostic : comprendre les deux formats de cj_raw_data"""
import sqlite3, json, os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'multiproshop.db')
conn = sqlite3.connect(DB_PATH)

# Format 1 : camelCase (categoryId)
rows1 = conn.execute("SELECT cj_raw_data FROM product WHERE cj_raw_data LIKE '%categoryId%' LIMIT 1").fetchall()
if rows1:
    d = json.loads(rows1[0][0])
    cat_id = d.get('categoryId', '')
    cat_name = d.get('categoryName', '')
    print(f"Format camelCase: categoryId={cat_id}, categoryName={cat_name}")

# Format 2 : snake_case (category_id)  
rows2 = conn.execute("SELECT cj_raw_data FROM product WHERE cj_raw_data LIKE '%category_id%' LIMIT 1").fetchall()
if rows2:
    d = json.loads(rows2[0][0])
    cat_id = d.get('category_id', '')
    cat_name = d.get('category_name', '')
    print(f"Format snake_case: category_id={cat_id}, category_name={cat_name}")
    print(f"  Toutes les clés: {sorted(d.keys())}")

# Compter chaque format
all_products = conn.execute("SELECT id, cj_raw_data FROM product WHERE cj_raw_data IS NOT NULL").fetchall()
camel = 0
snake = 0
both = 0
neither = 0
has_cat = 0

for pid, raw in all_products:
    d = json.loads(raw)
    has_camel = 'categoryId' in d and d['categoryId']
    has_snake = 'category_id' in d and d['category_id']
    if has_camel and has_snake:
        both += 1
    elif has_camel:
        camel += 1
    elif has_snake:
        snake += 1
    else:
        neither += 1
    
    # Vérifier si on peut extraire un category_id valide
    cid = d.get('categoryId') or d.get('category_id') or ''
    if cid:
        has_cat += 1

print(f"\nTotal produits: {len(all_products)}")
print(f"  Format camelCase uniquement: {camel}")
print(f"  Format snake_case uniquement: {snake}")
print(f"  Les deux: {both}")
print(f"  Aucun: {neither}")
print(f"  Avec un category_id exploitable: {has_cat}")

# Vérifier combien de ces category_id existent en base
all_cj_ids = set(r[0] for r in conn.execute('SELECT cj_category_id FROM category WHERE cj_category_id IS NOT NULL').fetchall())
found = 0
not_found = 0
for pid, raw in all_products:
    d = json.loads(raw)
    cid = d.get('categoryId') or d.get('category_id') or ''
    if cid:
        if cid in all_cj_ids:
            found += 1
        else:
            not_found += 1

print(f"\n  category_id trouvé en base CJ: {found}")
print(f"  category_id NON trouvé en base CJ: {not_found}")

# Exemples de category_id non trouvés
print(f"\n  Exemples category_id non trouvés:")
shown = 0
for pid, raw in all_products:
    d = json.loads(raw)
    cid = d.get('categoryId') or d.get('category_id') or ''
    if cid and cid not in all_cj_ids and shown < 5:
        cname = d.get('categoryName') or d.get('category_name') or ''
        print(f"    {cid} -> {cname}")
        shown += 1

conn.close()
