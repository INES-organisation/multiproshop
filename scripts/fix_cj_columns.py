"""
Script pour ajouter manuellement les colonnes CJ manquantes
"""
import sqlite3
import os

DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'instance',
    'multiproshop.db'
)

print("=" * 80)
print("CORRECTION: Ajout colonnes CJ manquantes")
print("=" * 80)
print(f"Base de données: {DB_PATH}\n")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Vérifier et ajouter cj_category_id
try:
    cursor.execute("ALTER TABLE category ADD COLUMN cj_category_id VARCHAR(255)")
    print("✓ Colonne cj_category_id ajoutée à category")
except sqlite3.OperationalError as e:
    if 'duplicate column' in str(e).lower():
        print("⚠ Colonne cj_category_id existe déjà")
    else:
        print(f"✗ Erreur cj_category_id: {e}")

# Vérifier et ajouter cj_pid
try:
    cursor.execute("ALTER TABLE product ADD COLUMN cj_pid VARCHAR(255)")
    print("✓ Colonne cj_pid ajoutée à product")
except sqlite3.OperationalError as e:
    if 'duplicate column' in str(e).lower():
        print("⚠ Colonne cj_pid existe déjà")
    else:
        print(f"✗ Erreur cj_pid: {e}")

# Créer les index uniques
try:
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_category_cj_id ON category(cj_category_id)")
    print("✓ Index unique créé pour cj_category_id")
except Exception as e:
    print(f"⚠ Index cj_category_id: {e}")

try:
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_product_cj_pid ON product(cj_pid)")
    print("✓ Index unique créé pour cj_pid")
except Exception as e:
    print(f"⚠ Index cj_pid: {e}")

conn.commit()
conn.close()

print("\n✅ Correction terminée")
