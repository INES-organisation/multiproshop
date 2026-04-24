"""
Diagnostic : catégories CJ manquantes pour les 99 produits dans des N1
"""
import sqlite3, json, os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'multiproshop.db')

def run():
    conn = sqlite3.connect(DB_PATH)
    
    missing_ids = [
        'A6158EC0-C66D-456D-923C-E784EE432A02',
        '67E91AA2-83EE-44B5-A308-DEC0643FF53F',
        'CA7192AE-4B6A-40F6-9FB8-C7152AAA3001',
        '8E00C4BE-1E35-43E7-A891-6CAE58BB48CF',
        '8B95183C-E835-4B9D-97DB-E7708F1A89B9',
        '5CBE1FF8-3083-43DB-BBBF-81C301A9D5A8',
        '240F64DA-9C68-4C61-BDE5-33302BE84535',
    ]
    
    print("=== CATÉGORIES CJ MANQUANTES EN BASE ===")
    for cj_id in missing_ids:
        row = conn.execute(
            "SELECT id, name, name_fr, level, parent_id FROM category WHERE cj_category_id = ?",
            (cj_id,)
        ).fetchone()
        if row:
            parent = conn.execute("SELECT name, parent_id FROM category WHERE id = ?", (row[4],)).fetchone()
            gp = conn.execute("SELECT name FROM category WHERE id = ?", (parent[1],)).fetchone() if parent and parent[1] else None
            print(f"  CJ N{row[3]}: {row[1]} (fr: {row[2]})")
            print(f"    parent: {parent[0] if parent else '?'} | grandparent: {gp[0] if gp else '?'}")
        else:
            print(f"  {cj_id}: PAS EN BASE CJ")
    
    # IDs numériques
    print("\n=== PRODUITS AVEC IDS NUMÉRIQUES ===")
    products = conn.execute("""
        SELECT p.id, p.name, p.cj_raw_data
        FROM product p
        JOIN category c ON c.id = p.category_id AND c.level = 1 AND c.cj_category_id IS NULL
        WHERE p.cj_raw_data IS NOT NULL
    """).fetchall()
    
    numeric_ids = {}
    for pid, pname, raw_json in products:
        try:
            raw = json.loads(raw_json)
            cid = str(raw.get('categoryId') or raw.get('category_id') or '')
            if cid.isdigit():
                if cid not in numeric_ids:
                    cat_name = raw.get('categoryName') or raw.get('category_name') or ''
                    numeric_ids[cid] = {'name': cat_name, 'count': 0, 'example': pname[:60]}
                numeric_ids[cid]['count'] += 1
        except:
            pass
    
    for nid, info in sorted(numeric_ids.items()):
        print(f"  ID={nid}: {info['count']}x | categoryName=\"{info['name']}\" | ex: {info['example']}")
    
    conn.close()

if __name__ == '__main__':
    run()
