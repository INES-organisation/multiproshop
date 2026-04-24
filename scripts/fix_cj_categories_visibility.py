"""
Script pour corriger la visibilité des catégories CJ existantes
Marque toutes les catégories CJ comme visible=False pour qu'elles n'apparaissent que dans l'admin
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from models.category import Category

def fix_cj_categories_visibility():
    """Marquer toutes les catégories CJ comme non visibles sur le site"""
    
    with app.app_context():
        print("\n" + "="*80)
        print("CORRECTION DE LA VISIBILITÉ DES CATÉGORIES CJ")
        print("="*80)
        
        # Récupérer toutes les catégories CJ
        cj_categories = Category.query.filter(
            Category.cj_category_id.isnot(None)
        ).all()
        
        print(f"\n📁 Catégories CJ trouvées: {len(cj_categories)}")
        
        if len(cj_categories) == 0:
            print("\n✓ Aucune catégorie CJ à corriger")
            return
        
        # Compter celles qui sont actuellement visibles
        visible_count = sum(1 for cat in cj_categories if cat.visible)
        print(f"   - Actuellement visibles: {visible_count}")
        print(f"   - Actuellement cachées: {len(cj_categories) - visible_count}")
        
        if visible_count == 0:
            print("\n✓ Toutes les catégories CJ sont déjà marquées comme non visibles")
            return
        
        # Marquer toutes comme non visibles
        print(f"\n🔧 Correction en cours...")
        updated = 0
        
        for category in cj_categories:
            if category.visible:
                category.visible = False
                updated += 1
                if updated <= 10:  # Afficher les 10 premières
                    print(f"   ✓ {category.name} → visible=False")
        
        # Sauvegarder
        db.session.commit()
        
        print(f"\n" + "="*80)
        print(f"✅ {updated} catégories CJ mises à jour")
        print("="*80)
        print("\n💡 Résultat:")
        print("   - Les catégories CJ n'apparaîtront plus sur le site public")
        print("   - Elles restent visibles dans l'admin CJ")
        print("   - Les catégories françaises restent visibles sur le site")
        print("\n🔄 Redémarrez le serveur Flask pour vider le cache\n")

if __name__ == '__main__':
    try:
        fix_cj_categories_visibility()
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
