"""Trouver et corriger le dernier produit encore dans un N1"""
import sqlite3, json, os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'multiproshop.db')

def run():
    conn = sqlite3.connect(DB_PATH)
    
    products = conn.execute("""
        SELECT p.id, p.name, p.cj_raw_data, c.name as cat_name, c.id as cat_id
        FROM product p
        JOIN category c ON c.id = p.category_id AND c.level = 1 AND c.cj_category_id IS NULL
    """).fetchall()
    
    print(f"{len(products)} produit(s) encore dans des N1:")
    
    for pid, pname, raw_json, cat_name, cat_id in products:
        print(f"\n  Product id={pid}: {pname}")
        print(f"  Catégorie actuelle: {cat_name} (id={cat_id})")
        
        if raw_json:
            try:
                raw = json.loads(raw_json)
                cj_cat_id = raw.get('categoryId') or raw.get('category_id') or ''
                cj_cat_name = raw.get('categoryName') or raw.get('category_name') or ''
                print(f"  CJ categoryId: {cj_cat_id}")
                print(f"  CJ categoryName: {cj_cat_name}")
                
                # Vérifier si un mapping existe
                mapping = conn.execute(
                    "SELECT mps_category_id FROM category_mapping WHERE external_category_id = ?",
                    (str(cj_cat_id),)
                ).fetchone()
                print(f"  Mapping existant: {mapping}")
                
                if not mapping and cj_cat_id:
                    # Pas de mapping, assigner manuellement
                    # Mode & Vêtements -> Vêtements Femme > Lingerie & Sous-vêtements > Divers
                    vet_femme = conn.execute(
                        "SELECT id FROM category WHERE name = 'Vêtements Femme' AND parent_id = 52 AND cj_category_id IS NULL"
                    ).fetchone()
                    if vet_femme:
                        # Trouver un N3 sous Vêtements Femme
                        n3 = conn.execute(
                            "SELECT id, name FROM category WHERE parent_id = ? AND cj_category_id IS NULL ORDER BY name LIMIT 1",
                            (vet_femme[0],)
                        ).fetchone()
                        if n3:
                            # Trouver un N4 sous ce N3
                            n4 = conn.execute(
                                "SELECT id, name FROM category WHERE parent_id = ? AND cj_category_id IS NULL ORDER BY name LIMIT 1",
                                (n3[0],)
                            ).fetchone()
                            if n4:
                                print(f"  -> Assignation: {cat_name} > Vêtements Femme > {n3[1]} > {n4[1]} (id={n4[0]})")
                                conn.execute("UPDATE product SET category_id = ? WHERE id = ?", (n4[0], pid))
                                
                                # Créer le mapping pour éviter le problème à l'avenir
                                provider_id = conn.execute("SELECT id FROM api_provider WHERE slug = 'cj-dropshipping'").fetchone()[0]
                                conn.execute("""
                                    INSERT INTO category_mapping (provider_id, external_category_id, external_category_name, mps_category_id, auto_import, apply_markup)
                                    VALUES (?, ?, ?, ?, 1, 1.3)
                                """, (provider_id, str(cj_cat_id), cj_cat_name, n4[0]))
                                print(f"  Mapping créé: {cj_cat_id} -> {n4[0]}")
            except Exception as e:
                print(f"  Erreur: {e}")
        else:
            print(f"  Pas de cj_raw_data")
    
    conn.commit()
    
    # Vérification
    remaining = conn.execute("""
        SELECT COUNT(*) FROM product p
        JOIN category c ON c.id = p.category_id AND c.level = 1 AND c.cj_category_id IS NULL
    """).fetchone()[0]
    print(f"\nProduits restants dans N1: {remaining}")
    
    conn.close()

if __name__ == '__main__':
    run()
