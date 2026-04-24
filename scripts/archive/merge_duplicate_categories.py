"""
Script pour fusionner les catégories en double
"""
from app import app
from extensions import db
from models.category import Category

def merge_categories():
    with app.app_context():
        print("\n" + "="*70)
        print("🔄 FUSION DES CATÉGORIES EN DOUBLE")
        print("="*70 + "\n")
        
        # Rechercher "Informatique" et "Informatique & Bureautique"
        informatique = Category.query.filter_by(name="Informatique", level=1).first()
        informatique_bureau = Category.query.filter_by(name="Informatique & Bureautique", level=1).first()
        
        if not informatique or not informatique_bureau:
            print("❌ Catégories non trouvées")
            if not informatique:
                print("   - 'Informatique' introuvable")
            if not informatique_bureau:
                print("   - 'Informatique & Bureautique' introuvable")
            return
        
        print(f"✅ Catégorie source: {informatique.name} (ID: {informatique.id})")
        print(f"   - {informatique.children.count()} sous-catégories")
        
        print(f"\n✅ Catégorie cible: {informatique_bureau.name} (ID: {informatique_bureau.id})")
        print(f"   - {informatique_bureau.children.count()} sous-catégories")
        
        # Déplacer toutes les sous-catégories de "Informatique" vers "Informatique & Bureautique"
        moved = 0
        for child in informatique.children.all():
            # Vérifier si une sous-catégorie avec le même nom existe déjà
            existing = Category.query.filter_by(
                name=child.name,
                parent_id=informatique_bureau.id,
                level=2
            ).first()
            
            if existing:
                print(f"   ⚠️  Sous-catégorie '{child.name}' existe déjà, fusion des items...")
                # Déplacer les items (niveau 3) vers la catégorie existante
                for item in child.children.all():
                    item.parent_id = existing.id
                    moved += 1
                # Supprimer la sous-catégorie en double
                db.session.delete(child)
            else:
                print(f"   ➡️  Déplacement: {child.name}")
                child.parent_id = informatique_bureau.id
                moved += 1
        
        # Supprimer la catégorie "Informatique" vide
        db.session.delete(informatique)
        db.session.commit()
        
        print(f"\n✅ Fusion terminée !")
        print(f"   - {moved} éléments déplacés")
        print(f"   - Catégorie 'Informatique' supprimée")
        print(f"   - Total sous-catégories dans '{informatique_bureau.name}': {informatique_bureau.children.count()}")
        print("="*70 + "\n")

if __name__ == "__main__":
    merge_categories()
