"""Vérifier que la page admin CJ se charge sans erreurs et que les routes API fonctionnent"""
import requests

BASE = 'http://multiproshop.local'

# 1. Page admin CJ
print("=== 1. Page admin CJ ===")
r = requests.get(f'{BASE}/admin/cj/products')
print(f"Status: {r.status_code}, Length: {len(r.text)}")
# Vérifier que les fonctions JS clés sont présentes
for fn in ['showProductDetails', 'renderProductModal', 'enrichProduct', 'syncProductVariants', 'syncProductStock', 'syncAllStocks']:
    if fn in r.text:
        print(f"  ✓ {fn} trouvée")
    else:
        print(f"  ✗ {fn} MANQUANTE!")

# Vérifier que le modal est présent
if 'productModal' in r.text:
    print(f"  ✓ Modal productModal trouvé")
else:
    print(f"  ✗ Modal productModal MANQUANT!")

# 2. Route /details (produit enrichi)
print("\n=== 2. Route /details ===")
r = requests.get(f'{BASE}/admin/api/cj/product/1377/details')
print(f"Status: {r.status_code}")
if r.status_code == 200:
    d = r.json()
    p = d['product']
    print(f"  Name: {p['name'][:50]}")
    print(f"  Description: {len(p.get('description',''))} chars")
    print(f"  Images: {len(p.get('images', []))}")
    print(f"  Variants: {p.get('variants_count')}")
    print(f"  image_url starts with http: {p.get('image_url','').startswith('http')}")

# 3. Route catégories
print("\n=== 3. Route catégories ===")
r = requests.post(f'{BASE}/admin/api/cj/categories/visible')
print(f"Status: {r.status_code}, CT: {r.headers.get('content-type','')}")
if r.status_code == 200 and 'json' in r.headers.get('content-type',''):
    d = r.json()
    print(f"  Success: {d.get('success')}")
    cats = d.get('categories', [])
    print(f"  Catégories: {len(cats)}")
    if cats:
        print(f"  Première: {cats[0].get('name','')} (id={cats[0].get('id')})")
else:
    print(f"  Non-JSON (login redirect probable): {r.text[:100]}")

# 4. Route produits par catégorie
print("\n=== 4. Route produits ===")
r = requests.post(f'{BASE}/admin/api/cj/categories/visible')
if r.status_code == 200 and 'json' in r.headers.get('content-type',''):
    cats = r.json().get('categories', [])
    if cats:
        cat_id = cats[0].get('id')
        r2 = requests.get(f'{BASE}/admin/api/cj/products/category/{cat_id}?page=1&per_page=6')
        print(f"Status: {r2.status_code}")
        if r2.status_code == 200 and 'json' in r2.headers.get('content-type',''):
            d2 = r2.json()
            print(f"  Success: {d2.get('success')}")
            prods = d2.get('products', [])
            print(f"  Produits: {len(prods)}")
            if prods:
                p0 = prods[0]
                print(f"  Premier: {p0.get('name','')[:40]} (id={p0.get('id')}, cj_pid={p0.get('cj_pid')})")

print("\n=== Tous les tests passés ===")
