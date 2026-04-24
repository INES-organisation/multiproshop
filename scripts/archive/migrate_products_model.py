"""
Script pour migrer le modèle Product vers la nouvelle structure
"""
from app import app
from extensions import db
from models.product import Product

def migrate_products():
    with app.app_context():
        print("\n" + "="*70)
        print("🔄 MIGRATION DU MODÈLE PRODUCT")
        print("="*70 + "\n")
        
        try:
            # Créer les nouvelles colonnes
            print("📝 Ajout des nouvelles colonnes...")
            db.create_all()
            print("✅ Colonnes ajoutées avec succès")
            
            # Mettre à jour les produits existants
            products = Product.query.all()
            print(f"\n📊 Mise à jour de {len(products)} produits existants...")
            
            for product in products:
                # Générer un slug si manquant
                if not product.slug:
                    from slugify import slugify
                    product.slug = slugify(product.name)
                
                # Définir is_active à True par défaut
                if not hasattr(product, 'is_active') or product.is_active is None:
                    product.is_active = True
                
                print(f"   ✓ {product.name}")
            
            db.session.commit()
            print(f"\n✅ Migration terminée avec succès !")
            print(f"   • {len(products)} produits mis à jour")
            print("="*70 + "\n")
            
        except Exception as e:
            print(f"❌ Erreur lors de la migration: {e}")
            db.session.rollback()

if __name__ == "__main__":
    migrate_products()
