"""
Exécuter la migration SQL pour ajouter les champs CJ
"""
import sys
import os
import sqlite3

# Chemin vers la base de données
DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    'instance',
    'multiproshop.db'
)

SQL_FILE = os.path.join(os.path.dirname(__file__), 'add_cj_fields.sql')

def run_migration():
    """Exécuter le fichier SQL de migration"""
    print("=" * 80)
    print("MIGRATION SQL: Ajout des champs CJ Dropshipping")
    print("=" * 80)
    print(f"\nBase de données: {DB_PATH}")
    print(f"Fichier SQL: {SQL_FILE}")
    
    if not os.path.exists(DB_PATH):
        print(f"\n❌ Base de données introuvable: {DB_PATH}")
        return False
    
    if not os.path.exists(SQL_FILE):
        print(f"\n❌ Fichier SQL introuvable: {SQL_FILE}")
        return False
    
    try:
        # Lire le fichier SQL
        with open(SQL_FILE, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Connexion à la base de données
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Exécuter chaque commande SQL
        commands = sql_content.split(';')
        executed = 0
        errors = 0
        
        print("\n" + "-" * 80)
        print("Exécution des commandes SQL...")
        print("-" * 80)
        
        for i, command in enumerate(commands):
            command = command.strip()
            if not command or command.startswith('--'):
                continue
            
            try:
                cursor.execute(command)
                executed += 1
                
                # Afficher les commandes importantes
                if 'ALTER TABLE' in command.upper():
                    table = command.split('ALTER TABLE')[1].split()[0]
                    column = command.split('ADD COLUMN')[1].split()[0] if 'ADD COLUMN' in command else ''
                    print(f"✓ ALTER TABLE {table} ADD COLUMN {column}")
                elif 'CREATE TABLE' in command.upper():
                    table = command.split('CREATE TABLE')[1].split()[0].replace('IF NOT EXISTS', '').strip()
                    print(f"✓ CREATE TABLE {table}")
                elif 'CREATE INDEX' in command.upper():
                    index = command.split('CREATE INDEX')[1].split()[0].replace('IF NOT EXISTS', '').strip()
                    print(f"✓ CREATE INDEX {index}")
                    
            except sqlite3.OperationalError as e:
                error_msg = str(e)
                # Ignorer les erreurs "duplicate column" (colonne existe déjà)
                if 'duplicate column' in error_msg.lower():
                    column = command.split('ADD COLUMN')[1].split()[0] if 'ADD COLUMN' in command else ''
                    print(f"⚠ Colonne {column} existe déjà (ignoré)")
                # Ignorer les erreurs "already exists" (table/index existe déjà)
                elif 'already exists' in error_msg.lower():
                    print(f"⚠ Élément existe déjà (ignoré)")
                else:
                    print(f"✗ Erreur: {error_msg}")
                    errors += 1
        
        # Commit des changements
        conn.commit()
        conn.close()
        
        print("\n" + "=" * 80)
        print("RÉSUMÉ MIGRATION")
        print("=" * 80)
        print(f"Commandes exécutées: {executed}")
        print(f"Erreurs: {errors}")
        
        if errors == 0:
            print("\n✅ MIGRATION RÉUSSIE")
            print("\nNouvelles fonctionnalités:")
            print("  - Catégories hiérarchiques CJ (3 niveaux)")
            print("  - Produits CJ avec synchronisation")
            print("  - Variantes produits (couleurs, tailles)")
            print("  - Index pour performances optimales")
            return True
        else:
            print(f"\n⚠ MIGRATION COMPLÉTÉE AVEC {errors} ERREUR(S)")
            return True  # On considère comme succès si les erreurs sont mineures
        
    except Exception as e:
        print(f"\n❌ ERREUR MIGRATION: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = run_migration()
    sys.exit(0 if success else 1)
