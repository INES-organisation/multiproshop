"""
Script de diagnostic: comprendre la structure des données retournées par get_product_details
et pourquoi _extract_variants_from_cj_data ne trouve pas les stocks
"""
import sys
import os
import json
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app
from extensions import db
from models.product import Product
from models.product_variant import ProductVariant
from services.api_providers.cj_dropshipping_optimized import CJDropshippingApiOptimized
from services.cj_variant_sync_service import CjVariantSyncService
from config import Config

def main():
    app = create_app()
    
    with app.app_context():
        product = Product.query.filter(Product.cj_pid.isnot(None)).first()
        
        print(f"\n{'='*80}")
        print(f"DIAGNOSTIC COMPLET - STRUCTURE DES DONNÉES")
        print(f"{'='*80}")
        print(f"Produit: {product.name[:60]}")
        print(f"CJ_PID: {product.cj_pid}")
        
        # Forcer le reset du rate limit cache
        from services.api_providers.cj_dropshipping_optimized import _memory_cache
        print(f"\n⏳ Reset du cache rate limit...")
        _memory_cache['rate_limit_until'] = 0
        _memory_cache['access_token'] = None
        _memory_cache['token_expires_at'] = 0
        
        print(f"⏳ Attente 10 secondes avant appel API...")
        time.sleep(10)
        
        cj_api = CJDropshippingApiOptimized(
            email=Config.CJ_EMAIL,
            password=Config.CJ_PASSWORD,
            dev_key=Config.CJ_DEV_KEY
        )
        
        print(f"\n--- TEST 1: get_product_details (retour formaté) ---")
        details = cj_api.get_product_details(product.cj_pid)
        if details:
            print(f"Type: {type(details)}")
            print(f"Clés: {list(details.keys())}")
            
            # Afficher les variantes formatées
            variants = details.get('variants', [])
            print(f"\nVariantes formatées: {len(variants)}")
            if variants:
                print(f"Premier variante - TOUTES les clés:")
                for k, v in variants[0].items():
                    print(f"  {k} = {v}")
            
            # Afficher le stock du produit
            print(f"\nStock produit: {details.get('stock')}")
            
            # Tester _extract_variants_from_cj_data avec ces données
            print(f"\n--- TEST 2: _extract_variants_from_cj_data ---")
            variant_service = CjVariantSyncService(cj_api)
            extracted = variant_service._extract_variants_from_cj_data(details)
            print(f"Variantes extraites: {len(extracted)}")
            if extracted:
                print(f"Premier variante extraite:")
                for k, v in extracted[0].items():
                    print(f"  {k} = {v}")
            else:
                print("AUCUNE VARIANTE EXTRAITE!")
                print(f"\nDébogage: cherche 'variants' dans les données...")
                print(f"  details.get('data', {{}}).get('variants') = {details.get('data', {}).get('variants') if isinstance(details.get('data'), dict) else 'data pas un dict'}")
                print(f"  details.get('data', {{}}).get('variantList') = {details.get('data', {}).get('variantList') if isinstance(details.get('data'), dict) else 'data pas un dict'}")
                print(f"  details.get('variants') = {type(details.get('variants'))} len={len(details.get('variants', []))}")
                print(f"  details.get('variantList') = {details.get('variantList')}")
        else:
            print("AUCUNE DONNÉE - API en rate limit ou erreur")
            print("Attendez quelques minutes et relancez le script")
        
        # TEST 3: Appel brut pour voir la structure réelle
        print(f"\n--- TEST 3: Appel brut _make_request ---")
        raw = cj_api._make_request('GET', 'product/query', params={'pid': product.cj_pid})
        if raw:
            print(f"Type: {type(raw)}")
            print(f"Clés: {list(raw.keys())}")
            data = raw.get('data', {})
            if isinstance(data, dict):
                print(f"Clés data: {list(data.keys())}")
                
                # Chercher les variantes brutes
                raw_variants = data.get('variants', [])
                print(f"\nVariantes brutes: {len(raw_variants)}")
                if raw_variants:
                    print(f"Premier variante brute - TOUTES les clés:")
                    for k, v in raw_variants[0].items():
                        print(f"  {k} = {v}")
                
                # Chercher tout ce qui ressemble à du stock
                stock_keys = [k for k in data.keys() if any(x in k.lower() for x in ['stock', 'quantity', 'sell', 'inventory'])]
                print(f"\nClés stock dans data: {stock_keys}")
                for k in stock_keys:
                    print(f"  {k} = {data[k]}")
        else:
            print("AUCUNE DONNÉE BRUTE")
        
        print(f"\n{'='*80}")
        print("FIN DU DIAGNOSTIC")
        print(f"{'='*80}")


if __name__ == '__main__':
    main()
