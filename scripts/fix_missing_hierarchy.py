"""
Corriger les 99 produits sans hiérarchie complète :
1. Créer les catégories MPS manquantes pour les CJ UUIDs absents
2. Mapper les IDs numériques vers des catégories existantes
3. Réassigner tous les produits vers le niveau le plus profond possible
"""
import sqlite3, json, os
from slugify import slugify

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'multiproshop.db')

# Mapping manuel des catégories CJ manquantes
# Format: cj_uuid -> (nom_fr, parent_mps_n2_ou_n3, cj_n1_parent)
# Basé sur les categoryName trouvés dans cj_raw_data
MISSING_CJ_CATS = {
    # Women's Clothing > Underwears > Bras
    'A6158EC0-C66D-456D-923C-E784EE432A02': {
        'name_fr': 'Soutiens-gorge',
        'cj_path': "Women's Clothing > Underwears > Bras",
        'target_n2': 'Vêtements Femme',  # sous Mode & Vêtements
        'target_n3': 'Lingerie & Sous-vêtements',  # à créer si n'existe pas
    },
    # Women's Clothing > Tops & Sets > Intimates
    '67E91AA2-83EE-44B5-A308-DEC0643FF53F': {
        'name_fr': 'Lingerie',
        'cj_path': "Women's Clothing > Tops & Sets > Intimates",
        'target_n2': 'Vêtements Femme',
        'target_n3': 'Lingerie & Sous-vêtements',
    },
    # Women's Clothing > Underwears > Panties
    'CA7192AE-4B6A-40F6-9FB8-C7152AAA3001': {
        'name_fr': 'Culottes',
        'cj_path': "Women's Clothing > Underwears > Panties",
        'target_n2': 'Vêtements Femme',
        'target_n3': 'Lingerie & Sous-vêtements',
    },
    # Health, Beauty & Hair > Massage & Relaxation
    '8E00C4BE-1E35-43E7-A891-6CAE58BB48CF': {
        'name_fr': 'Massage & Relaxation',
        'cj_path': "Health, Beauty & Hair > Massage & Relaxation",
        'target_n1': 'Santé & Beauté',
        'target_n2': 'Massage & Relaxation',  # à créer comme N2
        'level': 'n2',  # ce sera un N2 directement (pas de N3 nécessaire)
    },
    # Women's Clothing > Sleep & Lounge
    '8B95183C-E835-4B9D-97DB-E7708F1A89B9': {
        'name_fr': 'Pyjamas & Détente Femme',
        'cj_path': "Women's Clothing > Sleep & Lounge",
        'target_n2': 'Vêtements Femme',
        'target_n3': 'Lingerie & Sous-vêtements',
    },
    # Women's Clothing > Exotic Apparel
    '5CBE1FF8-3083-43DB-BBBF-81C301A9D5A8': {
        'name_fr': 'Tenues Fantaisie',
        'cj_path': "Women's Clothing > Exotic Apparel",
        'target_n2': 'Vêtements Femme',
        'target_n3': 'Lingerie & Sous-vêtements',
    },
    # Women's Clothing > Cosplay Costumes
    '240F64DA-9C68-4C61-BDE5-33302BE84535': {
        'name_fr': 'Costumes Cosplay',
        'cj_path': "Women's Clothing > Cosplay Costumes",
        'target_n2': 'Vêtements Femme',
        'target_n3': 'Hauts & Ensembles',  # existe déjà
    },
}

# IDs numériques -> catégorie MPS cible
NUMERIC_TARGETS = {
    '21': 'Maison, Jardin & Mobilier',  # packing material > box
    '22': 'Bijoux & Montres',           # Velvet Jewelry Storage Box
    '31': 'Informatique',               # Customized Cards
    '32': 'Informatique',               # Self-adhesive Labels
    '33': 'Informatique',               # Hang Tag
    '43': 'Maison, Jardin & Mobilier',  # Biodegradable Express Delivery Bags
}

MODE_MPS_ID = 52

def get_or_create_category(conn, name, slug_base, level, parent_id, existing_slugs):
    """Récupérer ou créer une catégorie MPS"""
    row = conn.execute(
        "SELECT id FROM category WHERE name = ? AND parent_id = ? AND cj_category_id IS NULL",
        (name, parent_id)
    ).fetchone()
    if row:
        return row[0], False
    
    slug = slugify(slug_base)
    base = slug
    counter = 1
    while slug in existing_slugs:
        slug = f"{base}-{counter}"
        counter += 1
    existing_slugs.add(slug)
    
    max_order = conn.execute(
        "SELECT COALESCE(MAX([order]), 0) FROM category WHERE parent_id = ?",
        (parent_id,)
    ).fetchone()[0] + 1
    
    conn.execute("""
        INSERT INTO category (name, name_fr, slug, level, parent_id, [order], is_active, visible, product_count)
        VALUES (?, ?, ?, ?, ?, ?, 1, 1, 0)
    """, (name, name, slug, level, parent_id, max_order))
    new_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    return new_id, True


def run():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('PRAGMA foreign_keys = OFF')
    
    provider_id = conn.execute("SELECT id FROM api_provider WHERE slug = 'cj-dropshipping'").fetchone()[0]
    existing_slugs = set(r[0] for r in conn.execute("SELECT slug FROM category").fetchall())
    
    # IDs des N2 sous Mode & Vêtements
    vet_femme_id = conn.execute(
        "SELECT id FROM category WHERE name = 'Vêtements Femme' AND parent_id = ? AND cj_category_id IS NULL",
        (MODE_MPS_ID,)
    ).fetchone()[0]
    
    print(f"Vêtements Femme: id={vet_femme_id}")
    
    # === ÉTAPE 1 : Créer les catégories manquantes pour les UUIDs ===
    print("\n=== ÉTAPE 1 : CATÉGORIES MANQUANTES (UUIDs) ===")
    
    created_cats = 0
    created_mappings = 0
    
    for cj_uuid, info in MISSING_CJ_CATS.items():
        name_fr = info['name_fr']
        
        if info.get('level') == 'n2':
            # Catégorie N2 directement sous un N1
            n1_name = info['target_n1']
            n1_id = conn.execute(
                "SELECT id FROM category WHERE name = ? AND level = 1 AND cj_category_id IS NULL",
                (n1_name,)
            ).fetchone()[0]
            
            # Créer N2
            n2_id, created = get_or_create_category(
                conn, info['target_n2'], f"{n1_name}-{info['target_n2']}", 2, n1_id, existing_slugs
            )
            if created:
                created_cats += 1
                print(f"  Créé N2: {info['target_n2']} (id={n2_id}) sous {n1_name}")
            
            # Créer N3 pour le produit
            n3_id, created = get_or_create_category(
                conn, name_fr, f"{n1_name}-{info['target_n2']}-{name_fr}", 3, n2_id, existing_slugs
            )
            if created:
                created_cats += 1
                print(f"  Créé N3: {name_fr} (id={n3_id}) sous {info['target_n2']}")
            
            target_id = n3_id
        else:
            # Catégorie N4 sous Vêtements Femme > N3
            target_n3_name = info['target_n3']
            
            # Créer ou récupérer le N3
            n3_id, created = get_or_create_category(
                conn, target_n3_name, f"mode-vetements-femme-{target_n3_name}", 3, vet_femme_id, existing_slugs
            )
            if created:
                created_cats += 1
                print(f"  Créé N3: {target_n3_name} (id={n3_id}) sous Vêtements Femme")
            
            # Créer N4
            n4_id, created = get_or_create_category(
                conn, name_fr, f"mode-vetements-femme-{target_n3_name}-{name_fr}", 4, n3_id, existing_slugs
            )
            if created:
                created_cats += 1
                print(f"  Créé N4: {name_fr} (id={n4_id}) sous {target_n3_name}")
            
            target_id = n4_id
        
        # Créer le mapping
        existing_mapping = conn.execute(
            "SELECT id FROM category_mapping WHERE external_category_id = ? AND provider_id = ?",
            (cj_uuid, provider_id)
        ).fetchone()
        
        if not existing_mapping:
            conn.execute("""
                INSERT INTO category_mapping (provider_id, external_category_id, external_category_name, mps_category_id, auto_import, apply_markup)
                VALUES (?, ?, ?, ?, 1, 1.3)
            """, (provider_id, cj_uuid, info['cj_path'], target_id))
            created_mappings += 1
            print(f"  Mapping: {cj_uuid} -> MPS id={target_id} ({name_fr})")
    
    print(f"\n  {created_cats} catégories créées, {created_mappings} mappings créés")
    
    # === ÉTAPE 2 : Mapper les IDs numériques ===
    print("\n=== ÉTAPE 2 : IDS NUMÉRIQUES ===")
    
    for num_id, target_n1_name in NUMERIC_TARGETS.items():
        # Trouver le N1 MPS
        n1 = conn.execute(
            "SELECT id FROM category WHERE name = ? AND level = 1 AND cj_category_id IS NULL",
            (target_n1_name,)
        ).fetchone()
        if not n1:
            print(f"  ⚠ N1 '{target_n1_name}' non trouvé pour ID={num_id}")
            continue
        
        # Trouver un N3 "Divers" ou le premier N3 sous ce N1
        divers_id, created = get_or_create_category(
            conn, "Divers", f"{target_n1_name}-divers", 2, n1[0], existing_slugs
        )
        if created:
            created_cats += 1
            print(f"  Créé N2: Divers (id={divers_id}) sous {target_n1_name}")
        
        divers_n3_id, created = get_or_create_category(
            conn, "Autres", f"{target_n1_name}-divers-autres", 3, divers_id, existing_slugs
        )
        if created:
            created_cats += 1
            print(f"  Créé N3: Autres (id={divers_n3_id}) sous Divers")
        
        # Créer le mapping
        existing_mapping = conn.execute(
            "SELECT id FROM category_mapping WHERE external_category_id = ? AND provider_id = ?",
            (num_id, provider_id)
        ).fetchone()
        
        if not existing_mapping:
            conn.execute("""
                INSERT INTO category_mapping (provider_id, external_category_id, external_category_name, mps_category_id, auto_import, apply_markup)
                VALUES (?, ?, ?, ?, 1, 1.3)
            """, (provider_id, num_id, f"Numeric ID {num_id}", divers_n3_id))
            created_mappings += 1
            print(f"  Mapping: ID={num_id} -> {target_n1_name} > Divers > Autres (id={divers_n3_id})")
    
    conn.commit()
    
    # === ÉTAPE 3 : Réassigner TOUS les produits ===
    print("\n=== ÉTAPE 3 : RÉASSIGNATION GLOBALE ===")
    
    all_mappings = conn.execute(
        "SELECT external_category_id, mps_category_id FROM category_mapping WHERE provider_id = ?",
        (provider_id,)
    ).fetchall()
    cj_to_mps = {ext_id: mps_id for ext_id, mps_id in all_mappings}
    
    products = conn.execute(
        "SELECT id, cj_raw_data, category_id FROM product WHERE cj_raw_data IS NOT NULL"
    ).fetchall()
    
    moved = 0
    still_n1 = 0
    for pid, raw_json, current_cat_id in products:
        try:
            raw = json.loads(raw_json)
            product_cj_cat_id = str(raw.get('categoryId') or raw.get('category_id') or '')
            if product_cj_cat_id and product_cj_cat_id in cj_to_mps:
                target = cj_to_mps[product_cj_cat_id]
                if current_cat_id != target:
                    conn.execute("UPDATE product SET category_id = ? WHERE id = ?", (target, pid))
                    moved += 1
        except:
            pass
    
    conn.commit()
    print(f"  {moved} produits réassignés")
    
    # === VÉRIFICATION ===
    print(f"\n{'=' * 60}")
    print("VÉRIFICATION FINALE")
    print(f"{'=' * 60}")
    
    rows = conn.execute("""
        SELECT c.level, COUNT(p.id)
        FROM product p
        JOIN category c ON c.id = p.category_id AND c.cj_category_id IS NULL
        GROUP BY c.level ORDER BY c.level
    """).fetchall()
    
    for r in rows:
        print(f"  N{r[0]}: {r[1]} produits")
    
    # Produits encore dans N1
    n1_prods = conn.execute("""
        SELECT c.name, COUNT(p.id)
        FROM product p
        JOIN category c ON c.id = p.category_id AND c.cj_category_id IS NULL AND c.level = 1
        GROUP BY c.id ORDER BY COUNT(p.id) DESC
    """).fetchall()
    
    if n1_prods:
        print(f"\n  ⚠ Produits encore dans des N1:")
        for r in n1_prods:
            print(f"    {r[0]}: {r[1]}")
    else:
        print(f"\n  ✓ Aucun produit dans des N1")
    
    # Mode & Vêtements : vérifier N4
    mode_levels = conn.execute("""
        WITH RECURSIVE cat_tree AS (
            SELECT id, name, level FROM category WHERE id = 52
            UNION ALL
            SELECT c.id, c.name, c.level FROM category c
            JOIN cat_tree ct ON c.parent_id = ct.id
            WHERE c.cj_category_id IS NULL
        )
        SELECT ct.level, COUNT(p.id)
        FROM cat_tree ct
        JOIN product p ON p.category_id = ct.id
        GROUP BY ct.level ORDER BY ct.level
    """).fetchall()
    
    print(f"\n  Mode & Vêtements par niveau:")
    for r in mode_levels:
        status = "✓" if r[0] >= 4 else "⚠"
        print(f"    {status} N{r[0]}: {r[1]} produits")
    
    # Stats
    total_mps = conn.execute("SELECT COUNT(*) FROM category WHERE cj_category_id IS NULL").fetchone()[0]
    total_mappings = conn.execute("SELECT COUNT(*) FROM category_mapping").fetchone()[0]
    non_classe = conn.execute(
        "SELECT COUNT(*) FROM product WHERE category_id = (SELECT id FROM category WHERE slug = 'non-classe')"
    ).fetchone()[0]
    print(f"\n  Stats: {total_mps} cat MPS, {total_mappings} mappings, {non_classe} 'Non classé'")
    
    conn.close()
    print("\nDONE")


if __name__ == '__main__':
    run()
