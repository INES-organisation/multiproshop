"""
Diagnostic approfondi du problème SQLAlchemy
"""
import sqlite3
from app import app
from extensions import db
from models.category import Category

print("="*70)
print("🔍 DIAGNOSTIC SQLALCHEMY")
print("="*70)

# 1. Vérifier avec SQLite direct
print("\n1️⃣ VÉRIFICATION SQLITE DIRECTE:")
db_path = "instance/boutique.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM category")
count_sqlite = cursor.fetchone()[0]
print(f"   ✅ SQLite direct: {count_sqlite} catégories")
conn.close()

# 2. Vérifier avec SQLAlchemy
print("\n2️⃣ VÉRIFICATION SQLALCHEMY:")
with app.app_context():
    print(f"   🔧 DB URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print(f"   🔧 DB Engine: {db.engine.url}")
    
    # Test 1: Query simple
    try:
        categories = Category.query.all()
        print(f"   ✅ Query.all(): {len(categories)} catégories")
    except Exception as e:
        print(f"   ❌ Query.all() erreur: {e}")
    
    # Test 2: SQL brut via SQLAlchemy
    try:
        result = db.session.execute(db.text("SELECT COUNT(*) FROM category"))
        count_raw = result.scalar()
        print(f"   ✅ SQL brut: {count_raw} catégories")
    except Exception as e:
        print(f"   ❌ SQL brut erreur: {e}")
    
    # Test 3: Vérifier la table
    try:
        result = db.session.execute(db.text("SELECT name FROM sqlite_master WHERE type='table' AND name='category'"))
        table_exists = result.fetchone()
        print(f"   ✅ Table 'category' existe: {table_exists is not None}")
    except Exception as e:
        print(f"   ❌ Vérification table erreur: {e}")
    
    # Test 4: Lister quelques catégories
    if categories:
        print("\n   📋 Premières catégories:")
        for cat in categories[:5]:
            print(f"      - ID:{cat.id} {cat.name}")

print("\n" + "="*70)
print("🎯 CONCLUSION:")
if count_sqlite > 0 and len(categories) == 0:
    print("   ❌ PROBLÈME: SQLite voit les catégories mais pas SQLAlchemy!")
    print("   💡 Solution: Problème de session ou de cache SQLAlchemy")
elif count_sqlite > 0 and len(categories) > 0:
    print("   ✅ TOUT FONCTIONNE: Les deux voient les catégories")
    print("   💡 Le problème est ailleurs (template, route, etc.)")
else:
    print("   ❌ PROBLÈME: Aucune catégorie dans la BD!")
print("="*70)
