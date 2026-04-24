import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from models.category import Category
from models.product import Product
from models.product_variant import ProductVariant

def delete_all_cj_categories():
    """Supprime toutes les catégories CJ et leurs produits de la base de données"""
    with app.app_context():
        try:
            # Étape 1: Récupérer les IDs des produits CJ
            print("=" * 60)
            print("ÉTAPE 1: Identification des produits CJ")
            print("=" * 60)
            cj_products = Product.query.filter(Product.cj_pid.isnot(None)).all()
            cj_product_ids = [p.id for p in cj_products]
            product_count = len(cj_products)
            
            print(f"Nombre de produits CJ trouvés: {product_count}")
            
            if product_count == 0:
                print("Aucun produit CJ à supprimer.")
            else:
                # Étape 2: Supprimer les variantes des produits CJ
                print("\n" + "=" * 60)
                print("ÉTAPE 2: Suppression des variantes de produits CJ")
                print("=" * 60)
                cj_variants = ProductVariant.query.filter(ProductVariant.product_id.in_(cj_product_ids)).all()
                variant_count = len(cj_variants)
                
                print(f"Nombre de variantes CJ trouvées: {variant_count}")
                
                if variant_count > 0:
                    for variant in cj_variants:
                        db.session.delete(variant)
                    
                    db.session.commit()
                    print(f"\n✓ {variant_count} variantes CJ supprimées avec succès!")
                else:
                    print("Aucune variante CJ à supprimer.")
                
                # Étape 3: Supprimer les produits CJ
                print("\n" + "=" * 60)
                print("ÉTAPE 3: Suppression des produits CJ")
                print("=" * 60)
                
                for product in cj_products:
                    print(f"Suppression du produit: {product.name} (ID: {product.id}, CJ PID: {product.cj_pid})")
                    db.session.delete(product)
                
                db.session.commit()
                print(f"\n✓ {product_count} produits CJ supprimés avec succès!")
            
            # Étape 4: Supprimer toutes les catégories CJ
            print("\n" + "=" * 60)
            print("ÉTAPE 4: Suppression des catégories CJ")
            print("=" * 60)
            cj_categories = Category.query.filter(Category.cj_category_id.isnot(None)).all()
            category_count = len(cj_categories)
            
            print(f"Nombre de catégories CJ trouvées: {category_count}")
            
            if category_count == 0:
                print("Aucune catégorie CJ à supprimer.")
                return
            
            for category in cj_categories:
                print(f"Suppression de: {category.name} (ID: {category.id}, CJ ID: {category.cj_category_id})")
                db.session.delete(category)
            
            db.session.commit()
            print(f"\n✓ {category_count} catégories CJ supprimées avec succès!")
            
            print("\n" + "=" * 60)
            print(f"RÉSUMÉ: {product_count} produits et {category_count} catégories CJ supprimés")
            print("=" * 60)
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Erreur lors de la suppression: {str(e)}")
            raise

if __name__ == '__main__':
    delete_all_cj_categories()
