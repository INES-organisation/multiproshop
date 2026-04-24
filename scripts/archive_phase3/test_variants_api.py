"""
Script pour tester l'API des variantes
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from models.product import Product
from models.product_variant import ProductVariant

def test_variants_api():
    with app.app_context():
        print("\n" + "="*80)
        print("TEST API VARIANTES")
        print("="*80 + "\n")
        
        # Trouver un produit avec variantes
        product = Product.query.join(ProductVariant).filter(
            ProductVariant.active == True
        ).first()
        
        if not product:
            print("❌ Aucun produit avec variantes trouvé\n")
            return
        
        print(f"Produit test: {product.name[:60]}")
        print(f"ID: {product.id}\n")
        
        # Vérifier les variantes en BDD
        variants_db = ProductVariant.query.filter_by(
            product_id=product.id,
            active=True
        ).all()
        
        print(f"Variantes en BDD: {len(variants_db)}")
        for v in variants_db[:3]:
            print(f"  • {v.color} - {v.size} | ${v.price}")
        
        # Tester l'API avec le client de test Flask
        with app.test_client() as client:
            print("\n" + "="*80)
            print("TEST API /api/variants/product/<id>/summary")
            print("="*80 + "\n")
            
            response = client.get(f'/api/variants/product/{product.id}/summary')
            
            print(f"Status: {response.status_code}")
            print(f"Response: {response.get_json()}\n")
            
            if response.status_code == 200:
                data = response.get_json()
                if data.get('success'):
                    summary = data.get('summary', {})
                    print(f"✓ API fonctionne")
                    print(f"  Has variants: {summary.get('has_variants')}")
                    print(f"  Total: {summary.get('total_variants')}")
                    print(f"  Couleurs: {summary.get('colors')}")
                    print(f"  Tailles: {summary.get('sizes')}")
                else:
                    print(f"❌ API retourne success=False")
                    print(f"   Message: {data.get('message')}")
            else:
                print(f"❌ Erreur HTTP {response.status_code}")

if __name__ == '__main__':
    test_variants_api()
