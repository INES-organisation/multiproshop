"""
Test: vérifier que la correction du stock fonctionne
Fait UN appel API et vérifie que le stock est bien extrait depuis inventories
"""
import sys
import os
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app
from extensions import db
from models.product import Product
from models.product_variant import ProductVariant
from services.api_providers.cj_dropshipping_optimized import CJDropshippingApiOptimized, _memory_cache
from services.cj_variant_sync_service import CjVariantSyncService
from config import Config

def main():
    app = create_app()
    
    with app.app_context():
        # Reset rate limit
        _memory_cache['rate_limit_until'] = 0
        _memory_cache['access_token'] = None
        _memory_cache['token_expires_at'] = 0
        
        product = Product.query.filter(Product.cj_pid.isnot(None)).first()
        
        print(f"\n{'='*80}")
        print(f"TEST CORRECTION STOCK")
        print(f"{'='*80}")
        print(f"Produit: {product.name[:60]}")
        print(f"CJ_PID: {product.cj_pid}")
        print(f"Stock actuel en BDD: {product.stock}")
        
        # Variantes actuelles
        old_variants = ProductVariant.query.filter_by(product_id=product.id).all()
        print(f"Variantes en BDD: {len(old_variants)}")
        for v in old_variants:
            print(f"  VID: {v.cj_vid} | Stock: {v.stock} | Prix: {v.price}")
        
        print(f"\n⏳ Attente 5s avant appel API...")
        time.sleep(5)
        
        cj_api = CJDropshippingApiOptimized(
            email=Config.CJ_EMAIL,
            password=Config.CJ_PASSWORD,
            dev_key=Config.CJ_DEV_KEY
        )
        
        # Test 1: get_product_details avec correction
        print(f"\n--- TEST 1: get_product_details (avec correction inventories) ---")
        details = cj_api.get_product_details(product.cj_pid)
        if details:
            variants = details.get('variants', [])
            print(f"Variantes retournées: {len(variants)}")
            for v in variants:
                print(f"  VID: {v.get('vid')} | Stock: {v.get('stock')} | Prix: {v.get('price')} | Inventories: {v.get('inventories')}")
        else:
            print("❌ Pas de données (rate limit probable)")
            print("Attendez 2-3 minutes et relancez")
            return
        
        # Test 2: _extract_variants_from_cj_data
        print(f"\n--- TEST 2: _extract_variants_from_cj_data ---")
        variant_service = CjVariantSyncService(cj_api)
        extracted = variant_service._extract_variants_from_cj_data(details)
        print(f"Variantes extraites: {len(extracted)}")
        for v in extracted:
            print(f"  VID: {v.get('cj_vid')} | Stock: {v.get('stock')} | Prix: {v.get('price')}")
        
        # Test 3: sync_product_variants complet
        print(f"\n--- TEST 3: sync_product_variants (sync complète) ---")
        result = variant_service.sync_product_variants(product.id)
        print(f"Résultat: {result}")
        
        # Vérifier le résultat
        product.update_stock_from_variants()
        db.session.commit()
        
        new_variants = ProductVariant.query.filter_by(product_id=product.id).all()
        print(f"\n--- RÉSULTAT FINAL ---")
        print(f"Stock produit: {product.stock}")
        print(f"Variantes: {len(new_variants)}")
        for v in new_variants:
            print(f"  VID: {v.cj_vid} | Stock: {v.stock} | Prix: {v.price}")
        
        print(f"\n{'='*80}")
        print("FIN DU TEST")
        print(f"{'='*80}")


if __name__ == '__main__':
    main()
