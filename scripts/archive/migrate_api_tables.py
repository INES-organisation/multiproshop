"""
Script pour créer les tables API Provider
"""
from app import create_app
from extensions import db

app = create_app()

with app.app_context():
    print("\n" + "="*70)
    print("🔧 CRÉATION DES TABLES API PROVIDER")
    print("="*70 + "\n")
    
    try:
        # Créer toutes les tables (ne recrée pas celles qui existent)
        db.create_all()
        
        print("✅ Tables créées avec succès !")
        print("\nTables API créées :")
        print("  - api_provider")
        print("  - category_mapping")
        print("  - product_source")
        print("  - api_sync_log")
        
        print("\n" + "="*70)
        print("🎉 Migration terminée !")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        print("\n" + "="*70 + "\n")
