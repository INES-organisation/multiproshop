"""
Script pour synchroniser les variantes d'un produit test depuis CJ
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from models.product import Product
from models.product_variant import ProductVariant
from services.cj_sync_service import CjSyncService
from services.api_providers.cj_dropshipping_optimized import CJDropshippingApiOptimized
from extensions import db
from flask import current_app

def sync_product_variants(product_id=None):
    with app.app_context():
        print("\n" + "="*80)
        print("SYNCHRONISATION DES VARIANTES DE PRODUITS CJ")
        print("="*80 + "\n")
        
        # Initialiser l'API CJ
        email = current_app.config.get('CJ_API_EMAIL')
        password = current_app.config.get('CJ_API_PASSWORD')
        
        if not email or not password:
            print("❌ Configuration CJ API manquante")
            print("   Vérifiez CJ_API_EMAIL et CJ_API_PASSWORD dans .env\n")
            return
        
        cj_api = CJDropshippingApiOptimized(email, password)
        sync_service = CjSyncService(cj_api)
        
        # Sélectionner le produit
        if product_id:
            product = Product.query.get(product_id)
            if not product:
                print(f"❌ Produit {product_id} introuvable\n")
                return
            products = [product]
        else:
            # Prendre les 5 premiers produits CJ
            products = Product.query.filter(
                Product.cj_pid.isnot(None)
            ).limit(5).all()
        
        if not products:
            print("❌ Aucun produit CJ trouvé\n")
            return
        
        print(f"Produits à synchroniser: {len(products)}\n")
        
        total_variants = 0
        
        for product in products:
            print(f"\n{'='*80}")
            print(f"Produit: {product.name[:60]}")
            print(f"CJ PID: {product.cj_pid}")
            print('='*80)
            
            try:
                # Récupérer les détails depuis l'API CJ
                print("  Appel API CJ...")
                product_data = cj_api.get_product_details(product.cj_pid)
                
                if not product_data:
                    print("  ❌ Aucune donnée reçue de l'API")
                    continue
                
                print("  ✓ Données reçues")
                
                # Récupérer les variantes
                variants_data = product_data.get('variants', [])
                print(f"  Variantes dans l'API: {len(variants_data)}")
                
                if len(variants_data) == 0:
                    print("  ⚠️  Ce produit n'a pas de variantes")
                    continue
                
                # Supprimer les anciennes variantes
                old_count = ProductVariant.query.filter_by(product_id=product.id).count()
                if old_count > 0:
                    ProductVariant.query.filter_by(product_id=product.id).delete()
                    print(f"  ✓ {old_count} anciennes variantes supprimées")
                
                # Créer les nouvelles variantes
                created = 0
                for variant_data in variants_data:
                    vid = variant_data.get('vid')
                    if not vid:
                        continue
                    
                    # Extraire couleur et taille depuis variant_key
                    variant_key = variant_data.get('key', '')
                    parts = variant_key.split('-') if variant_key else []
                    color = parts[0] if len(parts) > 0 else None
                    size = parts[1] if len(parts) > 1 else None
                    
                    variant = ProductVariant(
                        product_id=product.id,
                        cj_vid=vid,
                        variant_key=variant_key,
                        color=color,
                        size=size,
                        price=variant_data.get('price'),
                        suggested_price=variant_data.get('suggested_price'),
                        stock=variant_data.get('stock', 0),
                        image_url=variant_data.get('image'),
                        weight=variant_data.get('weight'),
                        sku=variant_data.get('sku'),
                        active=True
                    )
                    db.session.add(variant)
                    created += 1
                
                db.session.commit()
                total_variants += created
                
                print(f"  ✓ {created} variantes créées")
                
                # Afficher quelques exemples
                if created > 0:
                    print("\n  Exemples de variantes:")
                    samples = ProductVariant.query.filter_by(
                        product_id=product.id
                    ).limit(5).all()
                    
                    for v in samples:
                        display = f"{v.color or 'N/A'} - {v.size or 'N/A'}"
                        print(f"    • {display:<20} | ${v.price:.2f} | Stock: {v.stock}")
                
            except Exception as e:
                print(f"  ❌ Erreur: {e}")
                db.session.rollback()
                continue
        
        print("\n" + "="*80)
        print("RÉSUMÉ")
        print("="*80)
        print(f"\nProduits traités: {len(products)}")
        print(f"Total variantes créées: {total_variants}")
        
        # Vérification finale
        total_in_db = ProductVariant.query.filter_by(active=True).count()
        print(f"Variantes actives en BDD: {total_in_db}")
        
        print("\n✅ Synchronisation terminée !\n")

if __name__ == '__main__':
    import sys
    product_id = int(sys.argv[1]) if len(sys.argv) > 1 else None
    sync_product_variants(product_id)
