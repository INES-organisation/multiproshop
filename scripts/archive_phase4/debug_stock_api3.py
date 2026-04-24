"""
Script de diagnostic: appel API CJ avec gestion du rate limit
Attend que le rate limit expire puis fait UN SEUL appel pour voir la structure
"""
import sys
import os
import json
import time
import requests
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app
from extensions import db
from models.product import Product
from models.product_variant import ProductVariant
from config import Config

def main():
    app = create_app()
    
    with app.app_context():
        product = Product.query.filter(Product.cj_pid.isnot(None)).first()
        
        print(f"\n{'='*80}")
        print(f"DIAGNOSTIC API CJ - APPEL DIRECT (sans client)")
        print(f"{'='*80}")
        print(f"Produit: {product.name[:60]}")
        print(f"CJ_PID: {product.cj_pid}")
        
        base_url = 'https://developers.cjdropshipping.com/api2.0/v1'
        
        # Étape 1: Obtenir un token
        print(f"\n--- ÉTAPE 1: Authentification ---")
        
        max_attempts = 5
        token = None
        
        for attempt in range(max_attempts):
            print(f"  Tentative {attempt+1}/{max_attempts}...")
            
            try:
                resp = requests.post(
                    f"{base_url}/authentication/getAccessToken",
                    json={'email': Config.CJ_EMAIL, 'password': Config.CJ_PASSWORD},
                    headers={'Content-Type': 'application/json'},
                    verify=False,
                    timeout=30
                )
                
                print(f"  HTTP Status: {resp.status_code}")
                
                if resp.status_code == 429:
                    wait = 60 * (attempt + 1)
                    print(f"  ⚠️ Rate limit 429 - attente {wait}s...")
                    time.sleep(wait)
                    continue
                
                data = resp.json()
                print(f"  result: {data.get('result')}")
                print(f"  code: {data.get('code')}")
                print(f"  message: {data.get('message')}")
                
                if data.get('result') and data.get('data', {}).get('accessToken'):
                    token = data['data']['accessToken']
                    print(f"  ✅ Token obtenu!")
                    break
                elif data.get('code') == 1600200:
                    wait = 60 * (attempt + 1)
                    print(f"  ⚠️ Rate limit code 1600200 - attente {wait}s...")
                    time.sleep(wait)
                    continue
                else:
                    print(f"  ❌ Échec: {data.get('message')}")
                    break
                    
            except Exception as e:
                print(f"  ❌ Erreur: {e}")
                time.sleep(30)
        
        if not token:
            print("\n❌ Impossible d'obtenir un token. L'API CJ est en rate limit.")
            print("Attendez 5-10 minutes et relancez le script.")
            return
        
        # Étape 2: Appeler product/query pour voir la structure brute
        print(f"\n--- ÉTAPE 2: product/query (données brutes) ---")
        time.sleep(2)
        
        headers = {
            'CJ-Access-Token': token,
            'Content-Type': 'application/json'
        }
        if Config.CJ_DEV_KEY:
            headers['CJ-DEV-KEY'] = Config.CJ_DEV_KEY
        
        resp = requests.get(
            f"{base_url}/product/query",
            params={'pid': product.cj_pid},
            headers=headers,
            verify=False,
            timeout=30
        )
        
        print(f"  HTTP Status: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"  result: {data.get('result')}")
            
            product_data = data.get('data', {})
            if isinstance(product_data, dict):
                print(f"\n  Clés data: {list(product_data.keys())}")
                
                # Chercher stock
                for k in product_data.keys():
                    if any(x in k.lower() for x in ['stock', 'quantity', 'sell', 'inventory']):
                        print(f"  📦 {k} = {product_data[k]}")
                
                # Chercher variantes
                variants_raw = product_data.get('variants', [])
                print(f"\n  Variantes brutes: {len(variants_raw)}")
                
                if variants_raw and len(variants_raw) > 0:
                    print(f"\n  PREMIÈRE VARIANTE - TOUTES LES CLÉS:")
                    for k, v in variants_raw[0].items():
                        print(f"    {k} = {v}")
                    
                    # Chercher spécifiquement les clés de stock dans les variantes
                    print(f"\n  CLÉS DE STOCK DANS LES VARIANTES:")
                    for k in variants_raw[0].keys():
                        if any(x in k.lower() for x in ['stock', 'quantity', 'sell', 'inventory']):
                            print(f"    📦 {k} = {variants_raw[0][k]}")
                else:
                    print("  ⚠️ Aucune variante dans product/query")
            else:
                print(f"  data n'est pas un dict: {type(product_data)}")
                print(f"  data = {str(product_data)[:500]}")
        elif resp.status_code == 429:
            print("  ⚠️ Rate limit 429")
        else:
            print(f"  Réponse: {resp.text[:500]}")
        
        # Étape 3: Appeler product/variant/query
        print(f"\n--- ÉTAPE 3: product/variant/query ---")
        time.sleep(2)
        
        resp = requests.get(
            f"{base_url}/product/variant/query",
            params={'pid': product.cj_pid},
            headers=headers,
            verify=False,
            timeout=30
        )
        
        print(f"  HTTP Status: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"  result: {data.get('result')}")
            
            variant_data = data.get('data', [])
            if isinstance(variant_data, list) and len(variant_data) > 0:
                print(f"  Variantes: {len(variant_data)}")
                print(f"\n  PREMIÈRE VARIANTE - TOUTES LES CLÉS:")
                for k, v in variant_data[0].items():
                    print(f"    {k} = {v}")
            elif isinstance(variant_data, dict):
                print(f"  Clés data: {list(variant_data.keys())}")
                for dk, dv in variant_data.items():
                    if isinstance(dv, list) and len(dv) > 0:
                        print(f"\n  {dk}: {len(dv)} éléments")
                        print(f"  PREMIER ÉLÉMENT - TOUTES LES CLÉS:")
                        for k, v in dv[0].items():
                            print(f"    {k} = {v}")
            else:
                print(f"  data = {str(variant_data)[:500]}")
        elif resp.status_code == 429:
            print("  ⚠️ Rate limit 429")
        else:
            print(f"  Réponse: {resp.text[:500]}")
        
        print(f"\n{'='*80}")
        print("FIN DU DIAGNOSTIC")
        print(f"{'='*80}")


if __name__ == '__main__':
    main()
