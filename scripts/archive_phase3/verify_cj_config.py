"""
Vérifier la configuration du provider CJ Dropshipping
"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), '..', 'instance', 'multiproshop.db')

if not os.path.exists(db_path):
    print(f"Base de données non trouvée: {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("""
    SELECT id, name, api_key, api_secret, api_endpoint, is_active 
    FROM api_provider 
    WHERE slug = 'cj-dropshipping'
""")

result = cursor.fetchone()
conn.close()

if result:
    print("Configuration CJ Dropshipping:")
    print(f"  ID: {result[0]}")
    print(f"  Nom: {result[1]}")
    print(f"  Email: {result[2]}")
    print(f"  API Key: {result[3][:10]}...")
    print(f"  Endpoint: {result[4]}")
    print(f"  Actif: {'Oui' if result[5] else 'Non'}")
else:
    print("Provider CJ Dropshipping non trouvé dans la base de données")
