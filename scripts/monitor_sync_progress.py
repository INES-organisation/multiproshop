"""
Script de monitoring de la progression de synchronisation des variantes
"""
from app import app
from models.product import Product
from models.product_variant import ProductVariant
import time
import sys

def check_progress():
    """Vérifier la progression de la synchronisation"""
    with app.app_context():
        total = Product.query.filter(
            Product.cj_pid.isnot(None),
            Product.published == True
        ).count()
        
        with_variants = Product.query.join(ProductVariant).distinct().count()
        without_variants = total - with_variants
        percentage = round(with_variants / total * 100, 1) if total > 0 else 0
        
        return {
            'total': total,
            'with_variants': with_variants,
            'without_variants': without_variants,
            'percentage': percentage
        }

if __name__ == '__main__':
    print("Monitoring de la synchronisation des variantes CJ")
    print("=" * 60)
    
    iterations = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    delay = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    
    for i in range(iterations):
        stats = check_progress()
        
        print(f"[{i*delay}s] {stats['with_variants']}/{stats['total']} produits = {stats['percentage']}% | Manquants: {stats['without_variants']}")
        
        if stats['percentage'] >= 99.5:
            print("\n✅ Objectif atteint ! Synchronisation quasi-complète.")
            break
        
        if i < iterations - 1:
            time.sleep(delay)
    
    print("\n" + "=" * 60)
    final_stats = check_progress()
    print(f"État final: {final_stats['percentage']}% complété")
    print(f"Produits avec variantes: {final_stats['with_variants']}")
    print(f"Produits sans variantes: {final_stats['without_variants']}")
