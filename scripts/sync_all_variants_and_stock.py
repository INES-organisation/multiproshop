"""
Script de synchronisation complète des variantes et stocks
pour tous les produits CJ publiés
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from extensions import db
from models.product import Product
from models.product_variant import ProductVariant
from services.api_providers.cj_dropshipping_optimized import CJDropshippingApiOptimized
from services.cj_sync_service import CjSyncService
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def main():
    """Synchroniser les variantes et stocks de tous les produits publiés"""
    app = create_app()
    
    with app.app_context():
        print("=" * 80)
        print("SYNCHRONISATION VARIANTES ET STOCKS - TOUS LES PRODUITS CJ")
        print("=" * 80)
        print(f"Démarrage: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Récupérer tous les produits CJ publiés
        products = Product.query.filter(
            Product.cj_pid.isnot(None),
            Product.published == True
        ).all()
        
        total_products = len(products)
        print(f"📦 Produits CJ publiés trouvés: {total_products}")
        print()
        
        if total_products == 0:
            print("❌ Aucun produit CJ publié trouvé.")
            return
        
        # Initialiser l'API CJ et le service de sync
        cj_api = CJDropshippingApiOptimized(
            email=os.getenv('CJ_EMAIL'),
            password=os.getenv('CJ_PASSWORD')
        )
        sync_service = CjSyncService(cj_api)
        
        # Statistiques
        stats = {
            'total': total_products,
            'success': 0,
            'errors': 0,
            'variants_created': 0,
            'variants_updated': 0,
            'stock_updated': 0,
            'skipped': 0
        }
        
        print("🔄 Début de la synchronisation...")
        print("-" * 80)
        
        for index, product in enumerate(products, 1):
            try:
                print(f"\n[{index}/{total_products}] Produit: {product.name[:50]}...")
                print(f"   CJ PID: {product.cj_pid}")
                
                # 1. Synchroniser les variantes
                print("   📋 Synchronisation des variantes...")
                
                # Récupérer les variantes depuis CJ
                variants_data = cj_api.get_product_variants(product.cj_pid)
                
                if not variants_data or 'data' not in variants_data:
                    print("   ⚠️  Pas de données variantes disponibles")
                    stats['skipped'] += 1
                    continue
                
                # L'API CJ retourne data directement comme une liste
                variants_list = variants_data.get('data', [])
                
                # Si data n'est pas une liste, c'est peut-être un dict avec 'list'
                if isinstance(variants_list, dict):
                    variants_list = variants_list.get('list', [])
                
                if not variants_list or len(variants_list) == 0:
                    print("   ⚠️  Aucune variante trouvée")
                    stats['skipped'] += 1
                    continue
                
                print(f"   ✅ {len(variants_list)} variantes trouvées")
                
                # Synchroniser chaque variante
                variants_created = 0
                variants_updated = 0
                
                for variant_data in variants_list:
                    vid = variant_data.get('vid')
                    if not vid:
                        continue
                    
                    # Vérifier si la variante existe
                    existing_variant = ProductVariant.query.filter_by(
                        product_id=product.id,
                        cj_vid=vid
                    ).first()
                    
                    if existing_variant:
                        # Mettre à jour
                        existing_variant.variant_key = variant_data.get('variantKey', '')
                        existing_variant.price = float(variant_data.get('variantSellPrice', 0))
                        existing_variant.suggested_price = float(variant_data.get('variantSugSellPrice', 0))
                        # Le stock peut être dans variantStock ou inventoryNum
                        stock = variant_data.get('variantStock') or variant_data.get('inventoryNum', 0)
                        existing_variant.stock = int(stock) if stock else 0
                        existing_variant.image_url = variant_data.get('variantImage', '')
                        existing_variant.weight = int(variant_data.get('variantWeight', 0)) if variant_data.get('variantWeight') else 0
                        existing_variant.sku = variant_data.get('variantSku', '')
                        existing_variant.updated_at = datetime.utcnow()
                        variants_updated += 1
                    else:
                        # Créer nouvelle variante
                        stock = variant_data.get('variantStock') or variant_data.get('inventoryNum', 0)
                        new_variant = ProductVariant(
                            product_id=product.id,
                            cj_vid=vid,
                            variant_key=variant_data.get('variantKey', ''),
                            price=float(variant_data.get('variantSellPrice', 0)),
                            suggested_price=float(variant_data.get('variantSugSellPrice', 0)),
                            stock=int(stock) if stock else 0,
                            image_url=variant_data.get('variantImage', ''),
                            weight=int(variant_data.get('variantWeight', 0)) if variant_data.get('variantWeight') else 0,
                            sku=variant_data.get('variantSku', ''),
                            active=True
                        )
                        db.session.add(new_variant)
                        variants_created += 1
                
                db.session.commit()
                
                print(f"   ✅ Variantes: {variants_created} créées, {variants_updated} mises à jour")
                stats['variants_created'] += variants_created
                stats['variants_updated'] += variants_updated
                
                # 2. Mettre à jour le stock total du produit
                product.update_stock_from_variants()
                db.session.commit()
                
                print(f"   ✅ Stock total mis à jour: {product.stock}")
                stats['stock_updated'] += 1
                stats['success'] += 1
                
                # Pause pour éviter le rate limiting CJ (très strict)
                if index % 5 == 0:
                    print("\n   ⏸️  Pause 10s pour éviter le rate limiting CJ...")
                    time.sleep(10)
                else:
                    print("   ⏸️  Pause 3s...")
                    time.sleep(3)
                
            except Exception as e:
                print(f"   ❌ ERREUR: {str(e)}")
                stats['errors'] += 1
                db.session.rollback()
                continue
        
        # Afficher les statistiques finales
        print("\n" + "=" * 80)
        print("📊 STATISTIQUES FINALES")
        print("=" * 80)
        print(f"Total produits traités:     {stats['total']}")
        print(f"✅ Succès:                  {stats['success']}")
        print(f"❌ Erreurs:                 {stats['errors']}")
        print(f"⚠️  Ignorés:                {stats['skipped']}")
        print(f"📋 Variantes créées:        {stats['variants_created']}")
        print(f"🔄 Variantes mises à jour:  {stats['variants_updated']}")
        print(f"📦 Stocks mis à jour:       {stats['stock_updated']}")
        print()
        print(f"Terminé: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

if __name__ == '__main__':
    main()
