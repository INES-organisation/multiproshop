"""
Test: utiliser listV2 pour trouver des produits AVEC stock,
puis vérifier si product/query retourne bien les inventories pour ces produits
"""
import sys
import os
import time
import requests
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app
from extensions import db
from models.product import Product
from models.product_variant import ProductVariant
from services.api_providers.cj_dropshipping_optimized import _memory_cache
from config import Config

def main():
    app = create_app()
    
    with app.app_context():
        print(f"\n{'='*80}")
        print(f"TEST: TROUVER DES PRODUITS AVEC STOCK VIA listV2")
        print(f"{'='*80}")
        
        base_url = 'https://developers.cjdropshipping.com/api2.0/v1'
        
        # Utiliser le token existant si disponible
        token = _memory_cache.get('access_token')
        if not token or _memory_cache.get('token_expires_at', 0) < time.time():
            print("⏳ Obtention d'un nouveau token...")
            _memory_cache['rate_limit_until'] = 0
            
            for attempt in range(5):
                resp = requests.post(
                    f"{base_url}/authentication/getAccessToken",
                    json={'email': Config.CJ_EMAIL, 'password': Config.CJ_PASSWORD},
                    headers={'Content-Type': 'application/json'},
                    verify=False, timeout=30
                )
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get('result'):
                        token = data['data']['accessToken']
                        print(f"✅ Token obtenu!")
                        break
                print(f"  Tentative {attempt+1} - HTTP {resp.status_code} - attente 60s...")
                time.sleep(60)
        
        if not token:
            print("❌ Impossible d'obtenir un token")
            return
        
        headers = {
            'CJ-Access-Token': token,
            'Content-Type': 'application/json'
        }
        if Config.CJ_DEV_KEY:
            headers['CJ-DEV-KEY'] = Config.CJ_DEV_KEY
        
        # Test 1: listV2 pour voir les stocks
        print(f"\n--- TEST 1: listV2 (avec warehouseInventoryNum) ---")
        time.sleep(2)
        
        resp = requests.get(
            f"{base_url}/product/listV2",
            params={'page': 1, 'size': 5, 'keyWord': 'phone case'},
            headers=headers, verify=False, timeout=30
        )
        
        print(f"HTTP: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            if data.get('result'):
                content = data.get('data', {}).get('content', [])
                for item in content:
                    products = item.get('productList', [])
                    for p in products:
                        pid = p.get('id')
                        name = p.get('nameEn', '')[:50]
                        inv = p.get('warehouseInventoryNum', 0)
                        total_inv = p.get('totalVerifiedInventory', 0)
                        print(f"  PID: {pid} | Stock: {inv} | Verified: {total_inv} | {name}")
                        
                        if inv and int(inv) > 0:
                            # Tester product/query sur ce produit avec stock
                            print(f"\n  --- product/query pour ce produit avec stock ---")
                            time.sleep(2)
                            
                            resp2 = requests.get(
                                f"{base_url}/product/query",
                                params={'pid': pid},
                                headers=headers, verify=False, timeout=30
                            )
                            
                            if resp2.status_code == 200:
                                data2 = resp2.json()
                                if data2.get('result'):
                                    pdata = data2.get('data', {})
                                    variants = pdata.get('variants', [])
                                    print(f"  Variantes: {len(variants)}")
                                    for v in variants[:3]:
                                        inv_data = v.get('inventories')
                                        inv_num = v.get('inventoryNum')
                                        print(f"    VID: {v.get('vid')}")
                                        print(f"    inventoryNum: {inv_num}")
                                        print(f"    inventories: {inv_data}")
                                        if inv_data and isinstance(inv_data, list):
                                            for i in inv_data:
                                                print(f"      countryCode: {i.get('countryCode')} | totalInventory: {i.get('totalInventory')}")
                            
                            # Un seul test suffit
                            print(f"\n{'='*80}")
                            print("FIN DU TEST")
                            print(f"{'='*80}")
                            return
            else:
                print(f"  Erreur: {data.get('message')}")
        
        # Test 2: product/list (ancien endpoint) pour comparer
        print(f"\n--- TEST 2: product/list ---")
        time.sleep(2)
        
        resp = requests.get(
            f"{base_url}/product/list",
            params={'pageNum': 1, 'pageSize': 5},
            headers=headers, verify=False, timeout=30
        )
        
        print(f"HTTP: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            if data.get('result'):
                products = data.get('data', {}).get('list', [])
                for p in products:
                    pid = p.get('pid')
                    name = p.get('productNameEn', '')[:50]
                    print(f"  PID: {pid} | {name}")
                    
                    # Chercher des clés de stock
                    stock_keys = [k for k in p.keys() if any(x in k.lower() for x in ['stock', 'quantity', 'inventory'])]
                    for k in stock_keys:
                        print(f"    {k} = {p[k]}")
        
        print(f"\n{'='*80}")
        print("FIN DU TEST")
        print(f"{'='*80}")


if __name__ == '__main__':
    main()
