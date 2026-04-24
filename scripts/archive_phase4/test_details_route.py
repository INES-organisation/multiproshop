"""Test rapide de la route /details"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app
from models.product import Product
import json

app = create_app()

with app.app_context():
    client = app.test_client()
    
    # Trouver un produit avec stock
    p = Product.query.filter(Product.cj_pid.isnot(None), Product.stock > 0).first()
    if not p:
        print("Aucun produit avec stock")
        exit(1)
    
    print(f"Test produit ID={p.id} PID={p.cj_pid} Stock={p.stock}")
    
    resp = client.get(f'/admin/api/cj/product/{p.id}/details')
    data = json.loads(resp.data)
    
    print(f"Success: {data.get('success')}")
    prod = data.get('product', {})
    print(f"Name: {prod.get('name', '')[:60]}")
    print(f"Stock: {prod.get('stock')}")
    print(f"Variants: {prod.get('variants_count')}")
    print(f"Description: {'Oui' if prod.get('description') else 'Non'}")
    print(f"Rating: {prod.get('rating_average')} ({prod.get('rating_count')} avis)")
    print(f"Weight: {prod.get('weight')}")
    print(f"Images: {len(prod.get('images', []))}")
    print(f"Material: {prod.get('material')}")
