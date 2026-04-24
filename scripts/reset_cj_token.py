"""
Réinitialiser le token CJ pour forcer un nouveau token
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'instance', 'multiproshop.db')

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("UPDATE api_provider SET access_token = NULL WHERE slug = 'cj-dropshipping'")
conn.commit()

print("✓ Token CJ réinitialisé")
print("  Un nouveau token sera généré lors de la prochaine synchronisation")

conn.close()
