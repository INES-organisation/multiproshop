"""Diagnostic : retrouver la catégorie CJ d'origine des produits"""
import sqlite3, json, os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'multiproshop.db')
conn = sqlite3.connect(DB_PATH)

# 1. Vérifier les produits avec cj_raw_data qui contiennent category_id dans le JSON formaté
products = conn.execute('SELECT id, cj_raw_data, cj_pid FROM product LIMIT 10').fetchall()

print("=== Exemples de cj_raw_data (clés) ===")
for pid, raw, cj_pid in products[:3]:
    if raw:
        try:
            d = json.loads(raw)
            # Afficher toutes les clés qui contiennent "cat" ou "entry"
            relevant = {k: str(v)[:100] for k, v in d.items() if any(x in k.lower() for x in ['cat', 'entry', 'type'])}
            print(f"\n  Product id={pid} cj_pid={cj_pid}:")
            for k, v in relevant.items():
                print(f"    {k}: {v}")
        except:
            pass

# 2. Vérifier si les produits sans categoryId ont un productType ou entryCode
print("\n=== Champs alternatifs pour identifier la catégorie ===")
has_productType = 0
productType_values = set()
for pid, raw, cj_pid in conn.execute('SELECT id, cj_raw_data, cj_pid FROM product WHERE cj_raw_data IS NOT NULL').fetchall():
    try:
        d = json.loads(raw)
        pt = d.get('productType', '')
        if pt:
            has_productType += 1
            productType_values.add(pt)
    except:
        pass
print(f"  Produits avec productType: {has_productType}")
print(f"  Valeurs distinctes productType: {len(productType_values)}")
if productType_values:
    print(f"  Exemples: {list(productType_values)[:10]}")

# 3. Vérifier si on peut retrouver la catégorie via le SKU pattern
print("\n=== Pattern SKU ===")
skus = conn.execute('SELECT sku FROM product WHERE sku IS NOT NULL LIMIT 10').fetchall()
for s in skus:
    print(f"  {s[0]}")

# 4. Vérifier si les cj_raw_data des produits SANS categoryId ont d'autres infos
print("\n=== Produits SANS categoryId - structure cj_raw_data ===")
no_cat = conn.execute("SELECT id, cj_raw_data FROM product WHERE cj_raw_data IS NOT NULL AND cj_raw_data NOT LIKE '%categoryId%' LIMIT 1").fetchone()
if no_cat:
    d = json.loads(no_cat[1])
    print(f"  Product id={no_cat[0]}, toutes les clés:")
    for k in sorted(d.keys()):
        print(f"    {k}: {str(d[k])[:80]}")

# 5. Vérifier si les produits SANS categoryId dans cj_raw_data ont quand même un champ category
no_cat_products = conn.execute("SELECT cj_raw_data FROM product WHERE cj_raw_data NOT LIKE '%categoryId%' AND cj_raw_data IS NOT NULL LIMIT 5").fetchall()
print(f"\n=== Produits sans 'categoryId' dans raw_data: {len(no_cat_products)} exemples ===")
for raw_json, in no_cat_products[:2]:
    d = json.loads(raw_json)
    print(f"  Clés: {list(d.keys())[:15]}...")

# 6. Compter les produits qui ont 'category_id' (pas 'categoryId') dans cj_raw_data
alt = conn.execute("SELECT COUNT(*) FROM product WHERE cj_raw_data LIKE '%category_id%'").fetchone()[0]
print(f"\n  Produits avec 'category_id' dans raw: {alt}")

conn.close()
