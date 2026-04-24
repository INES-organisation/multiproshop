"""
Routes pour la synchronisation par batch des produits API
"""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from functools import wraps
from models.api_provider import ApiProvider, CategoryMapping, ProductSource
from models.product import Product
from services.api_providers import get_provider_service
from extensions import db
from datetime import datetime
import time

def admin_required(f):
    """Décorateur pour vérifier que l'utilisateur est admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            return jsonify({'success': False, 'error': 'Accès non autorisé'}), 403
        return f(*args, **kwargs)
    return decorated_function

api_sync_bp = Blueprint('api_sync', __name__, url_prefix='/admin/api/sync')

@api_sync_bp.route('/batch/<int:provider_id>', methods=['POST'])
@login_required
@admin_required
def sync_batch(provider_id):
    """Synchroniser un batch de produits (10 max)"""
    try:
        data = request.get_json() or {}
        batch_size = min(int(data.get('batch_size', 10)), 10)
        category_offset = int(data.get('category_offset', 0))
        product_offset = int(data.get('product_offset', 0))
        
        provider = ApiProvider.query.get_or_404(provider_id)
        service = get_provider_service(provider)
        
        # Récupérer les mappings actifs
        priority_categories = ['Scarves & Wraps', 'Hats & Caps', 'Gloves & Mittens']
        
        all_mappings = CategoryMapping.query.filter_by(
            provider_id=provider_id,
            auto_import=True
        ).all()
        
        # Trier : prioritaires d'abord
        priority_mappings = [m for m in all_mappings if m.external_category_name in priority_categories]
        other_mappings = [m for m in all_mappings if m.external_category_name not in priority_categories]
        mappings = priority_mappings + other_mappings
        
        if category_offset >= len(mappings):
            return jsonify({
                'success': True,
                'completed': True,
                'message': 'Synchronisation terminée',
                'stats': {
                    'total_categories': len(mappings),
                    'processed_categories': category_offset
                }
            })
        
        # Traiter la catégorie courante
        mapping = mappings[category_offset]
        
        # Récupérer les produits
        result = service.get_products(
            category_id=mapping.external_category_id,
            page=1,
            limit=100
        )
        
        products = result.get('products', [])
        
        # Traiter le batch de produits
        batch_start = product_offset
        batch_end = min(batch_start + batch_size, len(products))
        
        created = 0
        updated = 0
        failed = 0
        
        for product_data in products[batch_start:batch_end]:
            try:
                # Vérifier si le produit existe
                source = ProductSource.query.filter_by(
                    provider_id=provider_id,
                    external_product_id=str(product_data.get('external_id', ''))
                ).first()
                
                if source:
                    # Mettre à jour
                    update_product_from_source(source, product_data, mapping)
                    updated += 1
                else:
                    # Créer
                    create_product_from_source(provider, product_data, mapping)
                    created += 1
                    
            except Exception as e:
                print(f"Erreur import produit: {e}")
                failed += 1
        
        # Calculer le prochain offset
        next_product_offset = batch_end
        next_category_offset = category_offset
        
        if next_product_offset >= len(products):
            # Passer à la catégorie suivante
            next_category_offset += 1
            next_product_offset = 0
        
        completed = next_category_offset >= len(mappings)
        
        return jsonify({
            'success': True,
            'completed': completed,
            'message': f'Batch traité: {created} créés, {updated} mis à jour, {failed} échecs',
            'stats': {
                'created': created,
                'updated': updated,
                'failed': failed,
                'current_category': mapping.external_category_name,
                'category_progress': f'{category_offset + 1}/{len(mappings)}',
                'product_progress': f'{batch_end}/{len(products)}',
                'next_category_offset': next_category_offset,
                'next_product_offset': next_product_offset
            }
        })
        
    except Exception as e:
        print(f"Erreur sync batch: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def create_product_from_source(provider, product_data, mapping):
    """Créer un produit MPS depuis une source externe"""
    price = float(product_data.get('price', 0)) * mapping.apply_markup
    compare_price = float(product_data.get('compare_price', 0)) * mapping.apply_markup
    
    images = product_data.get('images', [])
    image_url = images[0] if images and len(images) > 0 else None
    
    product = Product(
        name=product_data.get('name', 'Produit sans nom'),
        description=product_data.get('description', ''),
        price=price,
        compare_price=compare_price,
        stock=int(product_data.get('stock', 0)),
        sku=product_data.get('sku', f"{provider.slug}-{product_data.get('external_id', 'unknown')}"),
        category_id=mapping.mps_category_id,
        image_url=image_url,
        is_active=True
    )
    
    db.session.add(product)
    db.session.flush()
    
    source = ProductSource(
        product_id=product.id,
        provider_id=provider.id,
        external_product_id=str(product_data.get('external_id', '')),
        external_price=float(product_data.get('price', 0)),
        external_stock=int(product_data.get('stock', 0)),
        external_currency=product_data.get('currency', 'USD'),
        sync_status='synced',
        last_synced_at=datetime.utcnow()
    )
    
    raw_data = product_data.get('raw_data', {})
    if raw_data:
        source.set_raw_data(raw_data)
    
    db.session.add(source)
    db.session.commit()
    
    return product


def update_product_from_source(source, product_data, mapping):
    """Mettre à jour un produit MPS depuis sa source"""
    product = source.product
    
    price = float(product_data.get('price', 0)) * mapping.apply_markup
    compare_price = float(product_data.get('compare_price', 0)) * mapping.apply_markup
    
    product.price = price
    product.compare_price = compare_price
    product.stock = int(product_data.get('stock', 0))
    
    images = product_data.get('images', [])
    if images and len(images) > 0:
        product.image_url = images[0]
    
    source.external_price = float(product_data.get('price', 0))
    source.external_stock = int(product_data.get('stock', 0))
    source.sync_status = 'synced'
    source.last_synced_at = datetime.utcnow()
    
    raw_data = product_data.get('raw_data', {})
    if raw_data:
        source.set_raw_data(raw_data)
    
    db.session.commit()
