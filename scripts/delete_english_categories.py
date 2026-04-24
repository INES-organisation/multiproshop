import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from models.category import Category
from models.product import Product
from models.product_variant import ProductVariant
from models.api_provider import CategoryMapping

def delete_english_cj_categories():
    """Supprime les catégories CJ en anglais (celles sans cj_category_id mais en anglais)"""
    with app.app_context():
        try:
            # Liste des catégories françaises à conserver (niveau 1)
            french_categories = [
                'Électronique & High-Tech',
                'Informatique',
                'Téléphonie & Tablettes',
                'Mode & Vêtements',
                'Maison & Jardin',
                'Santé & Beauté',
                'Sports & Loisirs',
                'Bébés & Puériculture',
                'Jeux & Jouets',
                'Auto & Moto',
                'Bricolage & Outillage',
                'Alimentation & Boissons',
                'Animalerie',
                'Livres & Papeterie',
                'Culture & Divertissement',
                'Services & Bons Plans',
                'Immobilier & Véhicules'
            ]
            
            # Récupérer les IDs des catégories françaises et leurs enfants
            french_cat_ids = set()
            for cat_name in french_categories:
                cat = Category.query.filter_by(name=cat_name).first()
                if cat:
                    french_cat_ids.add(cat.id)
                    # Ajouter tous les enfants récursivement
                    def add_children(parent_id):
                        children = Category.query.filter_by(parent_id=parent_id).all()
                        for child in children:
                            french_cat_ids.add(child.id)
                            add_children(child.id)
                    add_children(cat.id)
            
            print(f"Catégories françaises à conserver: {len(french_cat_ids)}")
            
            # Récupérer toutes les catégories à supprimer (celles qui ne sont pas françaises)
            all_categories = Category.query.all()
            categories_to_delete = [cat for cat in all_categories if cat.id not in french_cat_ids]
            
            print(f"Catégories à supprimer: {len(categories_to_delete)}")
            
            if len(categories_to_delete) == 0:
                print("Aucune catégorie à supprimer.")
                return
            
            # Afficher quelques exemples
            print("\nExemples de catégories à supprimer:")
            for cat in categories_to_delete[:10]:
                print(f"  - {cat.name} (ID: {cat.id})")
            
            # Récupérer les IDs des catégories à supprimer
            category_ids_to_delete = [cat.id for cat in categories_to_delete]
            
            # Étape 1: Supprimer les mappings de catégories
            print("\n" + "=" * 60)
            print("ÉTAPE 1: Suppression des mappings de catégories")
            print("=" * 60)
            mappings_to_delete = CategoryMapping.query.filter(CategoryMapping.mps_category_id.in_(category_ids_to_delete)).all()
            print(f"Mappings à supprimer: {len(mappings_to_delete)}")
            
            for mapping in mappings_to_delete:
                db.session.delete(mapping)
            
            db.session.commit()
            print(f"✓ {len(mappings_to_delete)} mappings supprimés")
            
            # Étape 2: Récupérer les produits liés à ces catégories
            print("\n" + "=" * 60)
            print("ÉTAPE 2: Identification des produits liés")
            print("=" * 60)
            products_to_delete = Product.query.filter(Product.category_id.in_(category_ids_to_delete)).all()
            product_ids = [p.id for p in products_to_delete]
            print(f"Produits à supprimer: {len(products_to_delete)}")
            
            if len(products_to_delete) > 0:
                # Étape 3: Supprimer les variantes
                print("\n" + "=" * 60)
                print("ÉTAPE 3: Suppression des variantes")
                print("=" * 60)
                variants_to_delete = ProductVariant.query.filter(ProductVariant.product_id.in_(product_ids)).all()
                print(f"Variantes à supprimer: {len(variants_to_delete)}")
                
                for variant in variants_to_delete:
                    db.session.delete(variant)
                
                db.session.commit()
                print(f"✓ {len(variants_to_delete)} variantes supprimées")
                
                # Étape 4: Supprimer les produits
                print("\n" + "=" * 60)
                print("ÉTAPE 4: Suppression des produits")
                print("=" * 60)
                
                for product in products_to_delete:
                    db.session.delete(product)
                
                db.session.commit()
                print(f"✓ {len(products_to_delete)} produits supprimés")
            
            # Étape 5: Supprimer les catégories
            print("\n" + "=" * 60)
            print("ÉTAPE 5: Suppression des catégories")
            print("=" * 60)
            
            for category in categories_to_delete:
                db.session.delete(category)
            
            db.session.commit()
            print(f"✓ {len(categories_to_delete)} catégories supprimées")
            
            print("\n" + "=" * 60)
            print(f"RÉSUMÉ: {len(categories_to_delete)} catégories CJ supprimées")
            print("=" * 60)
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Erreur: {str(e)}")
            import traceback
            traceback.print_exc()
            raise

if __name__ == '__main__':
    delete_english_cj_categories()
