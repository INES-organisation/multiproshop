"""
Script de test du système de variantes
Vérifie que les variantes sont correctement synchronisées et fonctionnelles
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from models.product import Product
from models.product_variant import ProductVariant
from services.variant_service import VariantService

def test_variants_system():
    """Tester le système de variantes"""
    with app.app_context():
        print("\n" + "="*70)
        print("TEST SYSTÈME DE VARIANTES")
        print("="*70 + "\n")
        
        variant_service = VariantService()
        
        # 1. Trouver des produits avec variantes
        print("1. RECHERCHE DE PRODUITS AVEC VARIANTES")
        print("-" * 70)
        
        products_with_variants = Product.query.join(ProductVariant).filter(
            Product.cj_pid.isnot(None),
            ProductVariant.active == True
        ).distinct().limit(5).all()
        
        print(f"✓ {len(products_with_variants)} produits avec variantes trouvés\n")
        
        if not products_with_variants:
            print("⚠️  Aucun produit avec variantes trouvé")
            print("   Synchronisez d'abord des produits CJ avec variantes\n")
            return
        
        # 2. Tester chaque produit
        for i, product in enumerate(products_with_variants, 1):
            print(f"\n{i}. TEST PRODUIT: {product.name[:60]}")
            print("-" * 70)
            print(f"   ID: {product.id} | CJ PID: {product.cj_pid}")
            
            # Récupérer le résumé des variantes
            summary = variant_service.get_product_variants_summary(product.id)
            
            if summary['has_variants']:
                print(f"\n   ✓ {summary['total_variants']} variantes disponibles")
                print(f"   Couleurs: {', '.join(summary['colors']) if summary['colors'] else 'Aucune'}")
                print(f"   Tailles: {', '.join(summary['sizes']) if summary['sizes'] else 'Aucune'}")
                print(f"   Stock total: {summary['total_stock']}")
                
                if summary['price_range']:
                    pr = summary['price_range']
                    if pr['same']:
                        print(f"   Prix: ${pr['min']:.2f}")
                    else:
                        print(f"   Prix: ${pr['min']:.2f} - ${pr['max']:.2f}")
                
                # Afficher quelques variantes
                print("\n   EXEMPLES DE VARIANTES:")
                for variant in summary['variants'][:3]:
                    print(f"   • {variant['display_name']:<20} | Prix: ${variant['price']:.2f} | Stock: {variant['stock']}")
                
                # Test de sélection
                if summary['colors'] and summary['sizes']:
                    test_color = summary['colors'][0]
                    test_size = summary['sizes'][0]
                    
                    print(f"\n   TEST SÉLECTION: Couleur={test_color}, Taille={test_size}")
                    variant = variant_service.get_variant_by_options(
                        product.id, 
                        test_color, 
                        test_size
                    )
                    
                    if variant:
                        print(f"   ✓ Variante trouvée: {variant['display_name']}")
                        print(f"     Prix: ${variant['price']:.2f} | Stock: {variant['stock']}")
                        
                        # Test disponibilité
                        available, message = variant_service.check_variant_availability(
                            variant['id'], 
                            quantity=1
                        )
                        print(f"     Disponibilité: {'✓' if available else '✗'} {message}")
                    else:
                        print("   ✗ Variante non trouvée")
            else:
                print("   ⚠️  Aucune variante active")
        
        # 3. Statistiques globales
        print("\n" + "="*70)
        print("STATISTIQUES GLOBALES")
        print("="*70)
        
        total_variants = ProductVariant.query.filter_by(active=True).count()
        total_products_with_variants = Product.query.join(ProductVariant).filter(
            ProductVariant.active == True
        ).distinct().count()
        
        print(f"\n✓ {total_products_with_variants} produits avec variantes")
        print(f"✓ {total_variants} variantes actives au total")
        
        # Couleurs les plus courantes
        from sqlalchemy import func
        top_colors = ProductVariant.query.filter(
            ProductVariant.active == True,
            ProductVariant.color.isnot(None)
        ).with_entities(
            ProductVariant.color,
            func.count(ProductVariant.id).label('count')
        ).group_by(ProductVariant.color).order_by(func.count(ProductVariant.id).desc()).limit(5).all()
        
        if top_colors:
            print("\nTop 5 couleurs:")
            for color, count in top_colors:
                print(f"  • {color:<20} {count:>3} variantes")
        
        # Tailles les plus courantes
        top_sizes = ProductVariant.query.filter(
            ProductVariant.active == True,
            ProductVariant.size.isnot(None)
        ).with_entities(
            ProductVariant.size,
            func.count(ProductVariant.id).label('count')
        ).group_by(ProductVariant.size).order_by(func.count(ProductVariant.id).desc()).limit(5).all()
        
        if top_sizes:
            print("\nTop 5 tailles:")
            for size, count in top_sizes:
                print(f"  • {size:<20} {count:>3} variantes")
        
        print("\n" + "="*70)
        print("✅ TEST TERMINÉ")
        print("="*70)

if __name__ == '__main__':
    test_variants_system()
