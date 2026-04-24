"""
Script de nettoyage :
1. Dissocier tous les produits des catégories MPS (category_id = NULL)
2. Renommer "Maison & Jardin" en "Maison, Jardin & Mobilier"
3. Réordonner les catégories MPS N1 selon la liste fournie
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'multiproshop.db')

# Ordre souhaité par l'utilisateur (nom -> order)
ORDERED_CATEGORIES = {
    1:  ('Électronique & High-Tech', 'electronique-high-tech'),
    2:  ('Informatique', 'informatique'),
    3:  ('Téléphonie & Tablettes', 'telephonie-tablettes'),
    4:  ('Bijoux & Montres', 'bijoux-et-montres'),
    5:  ('Mode & Vêtements', 'mode-vetements'),
    6:  ('Maison, Jardin & Mobilier', 'maison-jardin-mobilier'),
    7:  ('Santé & Beauté', 'sante-beaute'),
    8:  ('Sports & Loisirs', 'sports-loisirs'),
    9:  ('Bébés & Puériculture', 'bebes-puericulture'),
    10: ('Jeux & Jouets', 'jeux-jouets'),
    11: ('Auto & Moto', 'auto-moto'),
    12: ('Bricolage & Outillage', 'bricolage-outillage'),
    13: ('Électroménagers', 'electromenagers'),
    14: ('Alimentation & Boissons', 'alimentation-boissons'),
    15: ('Animalerie', 'animalerie'),
    16: ('Livres & Papeterie', 'livres-papeterie'),
    17: ('Culture & Divertissement', 'culture-divertissement'),
    18: ('Services & Bons Plans', 'services-bons-plans'),
    19: ('Immobilier & Véhicules', 'immobilier-vehicules'),
    20: ('Produits Numériques', 'produits-numeriques'),
}


def cleanup():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('PRAGMA foreign_keys = OFF')

    print("=" * 60)
    print("NETTOYAGE PRODUITS + RÉORDONNANCEMENT MPS")
    print("=" * 60)

    # ETAPE 1 : Créer catégorie "Non classé" et y déplacer tous les produits MPS
    # Vérifier si "Non classé" existe déjà
    existing = conn.execute(
        "SELECT id FROM category WHERE slug = 'non-classe'"
    ).fetchone()

    if existing:
        non_classe_id = existing[0]
        print(f"\n[1/3] Catégorie 'Non classé' existe déjà (id={non_classe_id})")
    else:
        conn.execute(
            "INSERT INTO category (name, slug, level, [order], is_active, visible, product_count) "
            "VALUES ('Non classé', 'non-classe', 1, 0, 1, 0, 0)"
        )
        non_classe_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        print(f"\n[1/3] Catégorie 'Non classé' créée (id={non_classe_id}, cachée)")

    # Déplacer tous les produits des catégories MPS vers "Non classé"
    mps_ids = [r[0] for r in conn.execute(
        'SELECT id FROM category WHERE cj_category_id IS NULL AND id != ?', (non_classe_id,)
    ).fetchall()]

    if mps_ids:
        placeholders = ','.join('?' * len(mps_ids))
        count = conn.execute(
            f'UPDATE product SET category_id = ? WHERE category_id IN ({placeholders})',
            [non_classe_id] + mps_ids
        ).rowcount
        print(f"     {count} produits déplacés vers 'Non classé'")
    else:
        print("     Aucun produit à déplacer")

    # ETAPE 2 : Renommer + réordonner
    rows = conn.execute(
        'SELECT id, name, slug FROM category WHERE cj_category_id IS NULL AND level = 1'
    ).fetchall()

    # Créer un mapping nom actuel -> id
    name_to_id = {}
    for r in rows:
        name_to_id[r[1]] = r[0]

    # Cas spécial : "Maison & Jardin" -> "Maison, Jardin & Mobilier"
    if 'Maison & Jardin' in name_to_id:
        name_to_id['Maison, Jardin & Mobilier'] = name_to_id.pop('Maison & Jardin')

    print(f"\n[2/3] Renommage et réordonnancement :")
    updated = 0
    for order_num, (name, slug) in ORDERED_CATEGORIES.items():
        cat_id = name_to_id.get(name)
        if cat_id:
            conn.execute(
                'UPDATE category SET name = ?, slug = ?, [order] = ? WHERE id = ?',
                (name, slug, order_num, cat_id)
            )
            print(f"  {order_num:2d}. {name:35s} (id={cat_id}, slug={slug})")
            updated += 1
        else:
            print(f"  {order_num:2d}. {name:35s} *** NON TROUVÉE ***")

    print(f"  -> {updated} catégories mises à jour")

    conn.commit()

    # ETAPE 3 : Vérification
    print(f"\n[3/3] Vérification finale :")
    rows = conn.execute(
        'SELECT id, name, slug, [order] FROM category WHERE cj_category_id IS NULL AND level = 1 ORDER BY [order]'
    ).fetchall()
    for r in rows:
        prod_count = conn.execute(
            'SELECT COUNT(*) FROM product WHERE category_id = ?', (r[0],)
        ).fetchone()[0]
        print(f"  {r[3]:2d}. id={r[0]:5d} | {r[1]:35s} | slug={r[2]:30s} | {prod_count} produits")

    total_orphans = conn.execute(
        'SELECT COUNT(*) FROM product WHERE category_id IS NULL'
    ).fetchone()[0]
    print(f"\n  Produits sans catégorie (orphelins) : {total_orphans}")

    conn.close()
    print("\nDONE")


if __name__ == '__main__':
    cleanup()
