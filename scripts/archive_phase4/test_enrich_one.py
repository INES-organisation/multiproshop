"""Test enrichissement d'un produit avec stock pour vérifier que toutes les données sont récupérées"""
import sys
import time
import warnings
from pathlib import Path

warnings.filterwarnings('ignore', message='Unverified HTTPS request')
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app
from extensions import db
from models.product import Product
from models.product_variant import ProductVariant
from services.api_providers.cj_dropshipping_optimized import CJDropshippingApiOptimized, _memory_cache
from services.cj_sync_service import CjSyncService
from services.cj_variant_sync_service import CjVariantSyncService
from config import Config

app = create_app()

with app.app_context():
    # Trouver un produit avec stock
    product = Product.query.filter(
        Product.cj_pid.isnot(None),
        Product.stock > 0
    ).first()
    
    if not product:
        print("Aucun produit avec stock")
        exit(1)
    
    print(f"=== AVANT enrichissement ===")
    print(f"ID: {product.id} | PID: {product.cj_pid}")
    print(f"Nom: {product.name[:60]}")
    print(f"Stock: {product.stock}")
    print(f"Description: {'Oui' if product.description else 'Non'}")
    print(f"Images: {product.images or 'Aucune'}")
    print(f"Poids: {product.weight}")
    print(f"Matériau: {product.material}")
    print(f"Avis: {product.rating_count} (note: {product.rating_average})")
    
    variants_before = ProductVariant.query.filter_by(product_id=product.id).count()
    print(f"Variantes: {variants_before}")
    
    # Reset rate limit
    _memory_cache['rate_limit_until'] = 0
    
    # Initialiser les services
    cj_api = CJDropshippingApiOptimized(
        email=Config.CJ_EMAIL,
        password=Config.CJ_PASSWORD,
        dev_key=Config.CJ_DEV_KEY
    )
    
    print(f"\n=== Enrichissement en cours... ===")
    
    # 1. Détails produit
    print("1. Récupération détails produit...")
    details = cj_api.get_product_details(product.cj_pid)
    if details:
        print(f"   Nom CJ: {details.get('name', '')[:60]}")
        print(f"   Description: {'Oui' if details.get('description') else 'Non'} ({len(details.get('description', ''))} chars)")
        print(f"   Image: {details.get('image', '')[:60]}")
        print(f"   Images: {len(details.get('images', []))}")
        print(f"   Poids: {details.get('weight')}")
        print(f"   Matériau: {details.get('material')}")
        print(f"   Prix: {details.get('price')}")
        print(f"   Variantes CJ: {len(details.get('variants', []))}")
        
        # Sauvegarder
        import json
        if details.get('description'):
            product.description = details['description']
        if details.get('image'):
            product.image_url = details['image']
        if details.get('images'):
            product.images = json.dumps(details['images'])
        if details.get('weight'):
            try:
                product.weight = float(details['weight'])
            except:
                pass
        if details.get('material'):
            product.material = details['material']
        if details.get('raw_data'):
            product.cj_raw_data = json.dumps(details['raw_data'], default=str)
    else:
        print("   ÉCHEC: Pas de détails retournés")
    
    time.sleep(2)
    
    # 2. Avis clients
    print("\n2. Récupération avis clients...")
    comments = cj_api.get_product_comments(product.cj_pid, page=1, page_size=50)
    print(f"   Avis trouvés: {len(comments)}")
    if comments:
        total_rating = sum(c.get('rating', 0) for c in comments)
        avg = total_rating / len(comments)
        print(f"   Note moyenne: {avg:.1f}")
        product.rating_average = avg
        product.rating_count = len(comments)
        for c in comments[:3]:
            print(f"   - {c.get('author', 'Anon')}: {c.get('rating')}★ - {c.get('content', '')[:50]}")
    
    time.sleep(2)
    
    # 3. Variantes
    print("\n3. Synchronisation variantes...")
    variant_service = CjVariantSyncService(cj_api)
    var_result = variant_service.sync_product_variants(product.id)
    print(f"   Succès: {var_result.get('success')}")
    print(f"   Créées: {var_result.get('variants_created', 0)}")
    print(f"   Mises à jour: {var_result.get('variants_updated', 0)}")
    print(f"   Total: {var_result.get('total_variants', 0)}")
    
    # Mettre à jour stock depuis variantes
    product.update_stock_from_variants()
    
    from datetime import datetime
    product.cj_last_sync = datetime.utcnow()
    product.synced_at = datetime.utcnow()
    
    db.session.commit()
    
    # Résultat
    print(f"\n=== APRÈS enrichissement ===")
    print(f"Nom: {product.name[:60]}")
    print(f"Stock: {product.stock}")
    print(f"Description: {'Oui' if product.description else 'Non'} ({len(product.description or '')} chars)")
    print(f"Images: {len(product.get_images_list()) if product.images else 0}")
    print(f"Poids: {product.weight}")
    print(f"Matériau: {product.material}")
    print(f"Avis: {product.rating_count} (note: {product.rating_average})")
    
    variants_after = ProductVariant.query.filter_by(product_id=product.id).count()
    print(f"Variantes: {variants_after}")
    
    print(f"\n✅ Enrichissement terminé!")
