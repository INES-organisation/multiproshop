"""Test des routes live du serveur"""
import requests

BASE = 'http://multiproshop.local'
session = requests.Session()

# Login d'abord
print("=== Login ===")
r = session.get(f'{BASE}/admin/api/cj/product/3983/details')
print(f"Details status: {r.status_code}")
ct = r.headers.get('content-type', '')
print(f"Content-Type: {ct}")
if 'json' in ct:
    d = r.json()
    print(f"Success: {d.get('success')}")
    p = d.get('product', {})
    print(f"Name: {p.get('name', '')[:60]}")
    print(f"Stock: {p.get('stock')}")
    print(f"Variants: {p.get('variants_count')}")
    print(f"Description: {'Oui' if p.get('description') else 'Non'}")
    print(f"Rating: {p.get('rating_average')} ({p.get('rating_count')} avis)")
else:
    print(f"Non-JSON response (probablement login redirect)")
    print(f"Body: {r.text[:200]}")

print("\n=== Test route /stats ===")
r = session.get(f'{BASE}/admin/api/cj/stats')
print(f"Status: {r.status_code}, Content-Type: {r.headers.get('content-type','')}")
if 'json' in r.headers.get('content-type', ''):
    d = r.json()
    if d.get('success'):
        s = d['stats']
        print(f"Total: {s['products']['total']}")
        print(f"In stock: {s['products']['in_stock']}")
        print(f"Variants: {s['variants']['total']}")
else:
    print(f"Non-JSON (login redirect)")

print("\n=== Tests terminés ===")
