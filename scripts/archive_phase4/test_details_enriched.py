"""Test route /details pour le produit enrichi + test live server"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
import json

# Test via le serveur live
print("=== Test route /details via serveur live ===")
r = requests.get('http://multiproshop.local/admin/api/cj/product/1377/details')
print(f"Status: {r.status_code}")

if r.status_code == 200:
    d = r.json()
    p = d['product']
    print(f"Name: {p.get('name','')[:60]}")
    print(f"Description: {len(p.get('description',''))} chars")
    print(f"Stock: {p.get('stock')}")
    print(f"Weight: {p.get('weight')}")
    print(f"Images: {len(p.get('images', []))}")
    print(f"Rating: {p.get('rating_average')} ({p.get('rating_count')} avis)")
    print(f"Variants count: {p.get('variants_count')}")
    
    variants = p.get('variants', [])
    for v in variants:
        print(f"  Variant: {v.get('variant_key')} | stock={v.get('stock')} | price={v.get('price')} | sku={v.get('sku')}")
    
    # Vérifier les images
    if p.get('images'):
        for i, img in enumerate(p['images'][:3]):
            print(f"  Image {i+1}: {img[:80]}")
    
    print(f"\nOK - Route /details fonctionne correctement")
else:
    print(f"ERREUR: {r.text[:200]}")
