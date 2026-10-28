"""
Copie de la base SQLite de MultiProShop vers PostgreSQL, avec vérification ligne à ligne.

Usage (dans le conteneur, DATABASE_URL pointant sur la base PostgreSQL vide) :
    python scripts/migrate_sqlite_to_postgres.py /chemin/vers/multiproshop.db

1. crée le schéma à partir des modèles (db.create_all) ;
2. copie chaque table, parents avant enfants (et, pour les catégories, parent avant enfant) ;
3. recale les séquences des clés primaires ;
4. compare chaque table : nombre de lignes et empreinte SHA-256 de toutes les lignes.

La base cible doit être vide : le script refuse d'écrire dans une table qui contient déjà des lignes.
La base SQLite est ouverte en lecture seule.
"""
import hashlib
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import Column, MetaData, Table, create_engine, func, select, text

BATCH = 1000


def normalize(value):
    """Valeur comparable entre SQLite et PostgreSQL (types Python déjà convertis par SQLAlchemy)."""
    if isinstance(value, float):
        return repr(round(value, 6))
    if hasattr(value, 'isoformat'):
        return value.isoformat()
    return repr(value)


def typed_view(table, names):
    """Vue de la table limitée aux colonnes communes, avec les types du modèle."""
    return Table(table.name, MetaData(),
                 *[Column(c.name, c.type, primary_key=c.primary_key) for c in table.columns if c.name in names])


def table_digest(conn, table):
    order = list(table.primary_key.columns) or list(table.columns)
    h = hashlib.sha256()
    count = 0
    for row in conn.execute(select(table).order_by(*order)).yield_per(BATCH):
        h.update('\x1f'.join(normalize(v) for v in row).encode())
        h.update(b'\x1e')
        count += 1
    return count, h.hexdigest()


def self_ref_column(table):
    for fk in table.foreign_keys:
        if fk.column.table is table:
            return fk.parent.name, fk.column.name
    return None


def ordered_rows(rows, table):
    """Pour une table qui se référence elle-même : chaque parent avant ses enfants."""
    ref = self_ref_column(table)
    if not ref:
        return rows
    child_col, parent_col = ref
    done, pending, out = set(), list(rows), []
    while pending:
        rest = [r for r in pending if r[child_col] is not None and r[child_col] not in done]
        ready = [r for r in pending if r[child_col] is None or r[child_col] in done]
        if not ready:
            # Parent introuvable dans la source : on garde la ligne (contrainte violée = erreur explicite)
            ready, rest = rest, []
        out.extend(ready)
        done.update(r[parent_col] for r in ready)
        pending = rest
    return out


def copy_table(src_conn, dst_conn, src_table, dst_table):
    columns = [c.name for c in dst_table.columns if c.name in src_table.columns]
    rows = [dict(r._mapping) for r in src_conn.execute(select(*[src_table.c[c] for c in columns]))]
    rows = ordered_rows(rows, dst_table)
    for i in range(0, len(rows), BATCH):
        dst_conn.execute(dst_table.insert(), rows[i:i + BATCH])
    return len(rows)


def reset_sequence(dst_conn, table):
    pk = list(table.primary_key.columns)
    if len(pk) != 1 or pk[0].type.python_type is not int:
        return
    name = pk[0].name
    seq = dst_conn.execute(text("SELECT pg_get_serial_sequence(:t, :c)"),
                           {'t': f'"{table.name}"', 'c': name}).scalar()
    if seq:
        dst_conn.execute(text(f"SELECT setval('{seq}', COALESCE((SELECT MAX(\"{name}\") FROM \"{table.name}\"), 0) + 1, false)"))


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sqlite_path = os.path.abspath(sys.argv[1])
    if not os.path.exists(sqlite_path):
        sys.exit(f"Base SQLite introuvable : {sqlite_path}")
    if not os.getenv('DATABASE_URL', '').startswith(('postgresql', 'postgres://')):
        sys.exit("DATABASE_URL doit pointer sur la base PostgreSQL cible")

    logging.disable(logging.WARNING)
    from app import app  # crée l'application (et une partie du schéma) sur DATABASE_URL
    from extensions import db
    logging.disable(logging.NOTSET)
    # Second create_all : certains modèles ne sont importés que par les routes, après celui de create_app
    with app.app_context():
        db.create_all()

    src_engine = create_engine(f'sqlite:///file:{sqlite_path}?mode=ro&uri=true')
    dst_engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])

    # Tables présentes dans SQLite mais sans modèle (ex. webhook_log, créée par un script) :
    # schéma recopié tel quel depuis SQLite.
    reflected = MetaData()
    reflected.reflect(src_engine)
    extra = MetaData()
    for name, table in reflected.tables.items():
        if name not in db.metadata.tables and name != 'sqlite_sequence':
            # Types génériques (DATETIME SQLite → TIMESTAMP…), sans les défauts propres à SQLite
            Table(name, extra, *[Column(c.name, c.type.as_generic(), primary_key=c.primary_key,
                                        nullable=c.nullable) for c in table.columns])
    extra.create_all(dst_engine)

    plan = [t for t in db.metadata.sorted_tables if t.name in reflected.tables] + list(extra.sorted_tables)
    missing = [t.name for t in db.metadata.sorted_tables if t.name not in reflected.tables]

    with src_engine.connect() as src, dst_engine.connect() as dst:
        for table in plan:
            n = dst.execute(select(func.count()).select_from(table)).scalar()
            if n:
                sys.exit(f"La table {table.name} contient déjà {n} lignes : base cible non vide, arrêt.")
        dst.rollback()

        print(f"{'table':<28}{'copiées':>10}")
        with dst.begin():
            for dst_table in plan:
                # Lecture avec les types du modèle : dates, booléens et JSON convertis côté Python
                src_typed = typed_view(dst_table, reflected.tables[dst_table.name].columns)
                n = copy_table(src, dst, src_typed, dst_table)
                reset_sequence(dst, dst_table)
                print(f"{dst_table.name:<28}{n:>10}")

        print(f"\n{'vérification':<28}{'SQLite':>10}{'PostgreSQL':>12}  empreinte")
        errors = 0
        for dst_table in plan:
            view = typed_view(dst_table, reflected.tables[dst_table.name].columns)
            n_src, h_src = table_digest(src, view)
            n_dst, h_dst = table_digest(dst, view)
            ok = n_src == n_dst and h_src == h_dst
            errors += not ok
            print(f"{dst_table.name:<28}{n_src:>10}{n_dst:>12}  {'OK' if ok else 'DIFFÉRENT'}")

    if missing:
        print(f"\nTables des modèles absentes de SQLite (créées vides) : {', '.join(missing)}")
    if errors:
        sys.exit(f"\n{errors} table(s) différente(s) : ne pas basculer sur PostgreSQL.")
    print("\nCopie vérifiée : toutes les tables sont identiques.")


if __name__ == '__main__':
    main()
