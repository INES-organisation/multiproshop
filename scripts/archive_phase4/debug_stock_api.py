"""
Script de diagnostic: voir exactement ce que l'API CJ retourne pour les variantes
"""
import sys
import os
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app
from extensions import db
from models.product import Product
from models.product_variant import ProductVariant
from services.api_providers.cj_dropshipping_optimized import CJDropshippingApiOptimized
from config import Config

def main():
    app = create_app()
    
    with app.app_context():
        # Prendre 3 produits avec variantes
        products = Product.query.filter(
            Product.cj_pid.isnot(None),
            Product.id.in_(
                db.session.query(ProductVariant.product_id).distinct()
            )
        ).limit(3).all()
        
        if not products:
            products = Product.query.filter(Product.cj_pid.isnot(None)).limit(3).all()
        
        print(f"\n{'='*80}")
        print(f"DIAGNOSTIC API CJ - STOCKS")
        print(f"{'='*80}")
        
        cj_api = CJDropshippingApiOptimized(
            email=Config.CJ_EMAIL,
            password=Config.CJ_PASSWORD,
            dev_key=Config.CJ_DEV_KEY
        )
        
        for product in products:
            print(f"\n{'='*80}")
            print(f"PRODUIT: {product.name[:60]}")
            print(f"CJ_PID: {product.cj_pid}")
            print(f"Stock actuel en BDD: {product.stock}")
            print(f"{'='*80}")
            
            # 1. get_product_details
            print(f"\n--- get_product_details ---")
            details = cj_api.get_product_details(product.cj_pid)
            if details:
                print(f"Type: {type(details)}")
                print(f"Clés niveau 1: {list(details.keys()) if isinstance(details, dict) else 'PAS UN DICT'}")
                
                if isinstance(details, dict):
                    data = details.get('data', {})
                    if isinstance(data, dict):
                        print(f"Clés data: {list(data.keys())}")
                        
                        # Chercher TOUT ce qui ressemble à du stock
                        stock_keys = [k for k in data.keys() if 'stock' in k.lower() or 'quantity' in k.lower() or 'sell' in k.lower() or 'inventory' in k.lower()]
                        print(f"\nClés liées au stock: {stock_keys}")
                        for k in stock_keys:
                            print(f"  {k} = {data[k]}")
                        
                        # Chercher les variantes
                        variant_keys = [k for k in data.keys() if 'variant' in k.lower()]
                        print(f"\nClés liées aux variantes: {variant_keys}")
                        for k in variant_keys:
                            val = data[k]
                            if isinstance(val, list) and len(val) > 0:
                                print(f"  {k}: {len(val)} éléments")
                                # Afficher la première variante complète
                                first = val[0]
                                print(f"  Premier élément (TOUTES les clés):")
                                for vk, vv in first.items():
                                    print(f"    {vk} = {vv}")
                            else:
                                print(f"  {k} = {val}")
                    else:
                        print(f"data n'est pas un dict: {type(data)}")
                        print(f"data = {str(data)[:500]}")
            else:
                print("AUCUNE DONNÉE RETOURNÉE")
            
            # 2. get_product_variants (méthode séparée si elle existe)
            print(f"\n--- get_product_variants ---")
            try:
                variants = cj_api.get_product_variants(product.cj_pid)
                if variants:
                    print(f"Type: {type(variants)}")
                    if isinstance(variants, dict):
                        print(f"Clés: {list(variants.keys())}")
                        data = variants.get('data', variants)
                        if isinstance(data, list) and len(data) > 0:
                            print(f"Nombre de variantes: {len(data)}")
                            first = data[0]
                            print(f"Premier élément (TOUTES les clés):")
                            for vk, vv in first.items():
                                print(f"  {vk} = {vv}")
                        elif isinstance(data, dict):
                            print(f"Clés data: {list(data.keys())}")
                            # Chercher les listes dans data
                            for dk, dv in data.items():
                                if isinstance(dv, list) and len(dv) > 0:
                                    print(f"  {dk}: {len(dv)} éléments")
                                    first = dv[0]
                                    print(f"  Premier élément (TOUTES les clés):")
                                    for vk, vv in first.items():
                                        print(f"    {vk} = {vv}")
                    elif isinstance(variants, list) and len(variants) > 0:
                        print(f"Nombre de variantes: {len(variants)}")
                        first = variants[0]
                        print(f"Premier élément (TOUTES les clés):")
                        for vk, vv in first.items():
                            print(f"  {vk} = {vv}")
                else:
                    print("AUCUNE DONNÉE RETOURNÉE")
            except Exception as e:
                print(f"ERREUR: {e}")
            
            # 3. Vérifier les variantes en BDD
            print(f"\n--- Variantes en BDD ---")
            db_variants = ProductVariant.query.filter_by(product_id=product.id).limit(3).all()
            for v in db_variants:
                print(f"  VID: {v.cj_vid} | Stock: {v.stock} | Prix: {v.price} | Couleur: {v.color} | Taille: {v.size}")
        
        print(f"\n{'='*80}")
        print("FIN DU DIAGNOSTIC")
        print(f"{'='*80}")


if __name__ == '__main__':
    main()
