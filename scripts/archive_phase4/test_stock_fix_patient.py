"""
Test patient: attend que le rate limit expire puis teste la correction du stock
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
from services.api_providers.cj_dropshipping_optimized import CJDropshippingApiOptimized, _memory_cache
from services.cj_variant_sync_service import CjVariantSyncService
from config import Config

def wait_for_api():
    """Attendre que l'API CJ soit disponible"""
    base_url = 'https://developers.cjdropshipping.com/api2.0/v1'
    
    for attempt in range(10):
        print(f"  Tentative {attempt+1}/10...")
        try:
            resp = requests.post(
                f"{base_url}/authentication/getAccessToken",
                json={'email': Config.CJ_EMAIL, 'password': Config.CJ_PASSWORD},
                headers={'Content-Type': 'application/json'},
                verify=False,
                timeout=30
            )
            
            if resp.status_code == 200:
                data = resp.json()
                if data.get('result') and data.get('data', {}).get('accessToken'):
                    print(f"  ✅ API disponible!")
                    return data['data']['accessToken']
                elif data.get('code') == 1600200:
                    print(f"  ⚠️ Rate limit dans réponse - attente 60s...")
                    time.sleep(60)
                    continue
            elif resp.status_code == 429:
                print(f"  ⚠️ Rate limit 429 - attente 60s...")
                time.sleep(60)
                continue
            else:
                print(f"  ❌ HTTP {resp.status_code}")
                time.sleep(30)
        except Exception as e:
            print(f"  ❌ Erreur: {e}")
            time.sleep(30)
    
    return None

def main():
    app = create_app()
    
    with app.app_context():
        product = Product.query.filter(Product.cj_pid.isnot(None)).first()
        
        print(f"\n{'='*80}")
        print(f"TEST CORRECTION STOCK (avec attente rate limit)")
        print(f"{'='*80}")
        print(f"Produit: {product.name[:60]}")
        print(f"CJ_PID: {product.cj_pid}")
        print(f"Stock actuel en BDD: {product.stock}")
        
        # Variantes actuelles
        old_variants = ProductVariant.query.filter_by(product_id=product.id).all()
        print(f"Variantes en BDD: {len(old_variants)}")
        for v in old_variants:
            print(f"  VID: {v.cj_vid} | Stock: {v.stock} | Prix: {v.price}")
        
        # Attendre que l'API soit disponible
        print(f"\n⏳ Attente que l'API CJ soit disponible...")
        token = wait_for_api()
        
        if not token:
            print("❌ Impossible d'obtenir un token après 10 tentatives")
            return
        
        # Reset le cache et injecter le token
        _memory_cache['rate_limit_until'] = 0
        _memory_cache['access_token'] = token
        _memory_cache['token_expires_at'] = time.time() + (14 * 24 * 3600)
        
        cj_api = CJDropshippingApiOptimized(
            email=Config.CJ_EMAIL,
            password=Config.CJ_PASSWORD,
            dev_key=Config.CJ_DEV_KEY
        )
        
        # Test 1: Appel brut pour voir la structure
        print(f"\n--- TEST 1: Appel brut product/query ---")
        raw = cj_api._make_request('GET', 'product/query', params={'pid': product.cj_pid})
        if raw:
            raw_data = raw.get('data', {})
            if isinstance(raw_data, dict):
                raw_variants = raw_data.get('variants', [])
                print(f"Variantes brutes: {len(raw_variants)}")
                if raw_variants:
                    v = raw_variants[0]
                    print(f"  Clés: {list(v.keys())}")
                    print(f"  inventories: {v.get('inventories')}")
                    print(f"  inventoryNum: {v.get('inventoryNum')}")
                    print(f"  variantSellPrice: {v.get('variantSellPrice')}")
        else:
            print("❌ Pas de données brutes")
            return
        
        # Test 2: get_product_details (formaté)
        print(f"\n--- TEST 2: get_product_details (formaté avec correction) ---")
        time.sleep(2)
        details = cj_api.get_product_details(product.cj_pid)
        if details:
            variants = details.get('variants', [])
            print(f"Variantes formatées: {len(variants)}")
            for v in variants:
                print(f"  VID: {v.get('vid')} | Stock: {v.get('stock')} | Prix: {v.get('price')} | Inventories: {v.get('inventories')}")
        else:
            print("❌ Pas de données formatées")
            return
        
        # Test 3: _extract_variants_from_cj_data
        print(f"\n--- TEST 3: _extract_variants_from_cj_data ---")
        variant_service = CjVariantSyncService(cj_api)
        extracted = variant_service._extract_variants_from_cj_data(details)
        print(f"Variantes extraites: {len(extracted)}")
        for v in extracted:
            print(f"  VID: {v.get('cj_vid')} | Stock: {v.get('stock')} | Prix: {v.get('price')}")
        
        # Test 4: sync complet
        print(f"\n--- TEST 4: sync_product_variants ---")
        time.sleep(2)
        result = variant_service.sync_product_variants(product.id)
        print(f"Résultat: {result}")
        
        # Mettre à jour le stock
        product.update_stock_from_variants()
        db.session.commit()
        
        # Résultat final
        new_variants = ProductVariant.query.filter_by(product_id=product.id).all()
        print(f"\n{'='*80}")
        print(f"RÉSULTAT FINAL")
        print(f"{'='*80}")
        print(f"Stock produit: {product.stock}")
        print(f"Variantes: {len(new_variants)}")
        for v in new_variants:
            print(f"  VID: {v.cj_vid} | Stock: {v.stock} | Prix: {v.price}")
        
        if product.stock > 0:
            print(f"\n✅ SUCCÈS! Stock récupéré: {product.stock}")
        else:
            print(f"\n⚠️ Stock toujours à 0 - ce produit n'a peut-être pas d'inventaire CJ")
            print(f"   (inventories était None/vide dans la réponse API)")
        
        print(f"\n{'='*80}")


if __name__ == '__main__':
    main()
