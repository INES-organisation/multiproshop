"""
Script pour ajouter le champ stripe_session_id à la table Order
"""
from app import create_app
from extensions import db

app = create_app()

with app.app_context():
    try:
        # Ajouter la colonne stripe_session_id
        with db.engine.connect() as conn:
            conn.execute(db.text('ALTER TABLE "order" ADD COLUMN stripe_session_id VARCHAR(255)'))
            conn.commit()
        print("✅ Colonne stripe_session_id ajoutée avec succès!")
    except Exception as e:
        if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
            print("ℹ️  La colonne stripe_session_id existe déjà")
        else:
            print(f"❌ Erreur: {e}")
