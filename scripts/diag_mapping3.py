"""Diagnostic : comment les produits étaient-ils liés aux catégories ?"""
import sqlite3, json, os
from collections import Counter

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'multiproshop.db')
conn = sqlite3.connect(DB_PATH)

products = conn.execute('SELECT id, cj_raw_data FROM product WHERE cj_raw_data IS NOT NULL').fetchall()

# Analyser les champs catégorie disponibles
has_categoryId = 0
has_categoryName = 0
has_entryName = 0
has_entryCode = 0
empty_categoryId = 0
empty_categoryName = 0

cat_name_n1 = Counter()

for pid, raw_json in products:
    try:
        raw = json.loads(raw_json)
        cid = raw.get('categoryId', '')
        cname = raw.get('categoryName', '')
        ename = raw.get('entryName', '')
        ecode = raw.get('entryCode', '')
        
        if cid: has_categoryId += 1
        else: empty_categoryId += 1
        
        if cname: 
            has_categoryName += 1
            # Extraire le N1 du categoryName (avant le premier " > " ou " / ")
            n1 = cname.split(' > ')[0].split(' / ')[0].strip()
            cat_name_n1[n1] += 1
        else: 
            empty_categoryName += 1
        
        if ename: has_entryName += 1
        if ecode: has_entryCode += 1
    except:
        pass

print(f"=== Champs disponibles sur {len(products)} produits ===")
print(f"  categoryId non vide: {has_categoryId} / vide: {empty_categoryId}")
print(f"  categoryName non vide: {has_categoryName} / vide: {empty_categoryName}")
print(f"  entryName non vide: {has_entryName}")
print(f"  entryCode non vide: {has_entryCode}")

print(f"\n=== categoryName N1 (top 30) ===")
for name, count in cat_name_n1.most_common(30):
    print(f"  {count:6d} | {name}")

# Vérifier si les produits sans categoryId ont un categoryName
print(f"\n=== Produits SANS categoryId mais AVEC categoryName ===")
count = 0
for pid, raw_json in products:
    try:
        raw = json.loads(raw_json)
        if not raw.get('categoryId') and raw.get('categoryName'):
            count += 1
    except:
        pass
print(f"  {count} produits")

conn.close()
