"""
Routes pour les webhooks des providers
Permet de recevoir des mises à jour en temps réel
"""
from flask import Blueprint, request, jsonify
from extensions import db
from models.api_provider import ApiProvider, ProductSource, ApiSyncLog
from models.product import Product
from datetime import datetime
import hmac
import hashlib

webhooks_bp = Blueprint('webhooks', __name__, url_prefix='/webhooks')

@webhooks_bp.route('/cj-dropshipping', methods=['POST'])
def cj_webhook():
    """Webhook pour CJ Dropshipping"""
    try:
        data = request.json
        
        # Vérifier la signature (sécurité)
        signature = request.headers.get('X-CJ-Signature', '')
        if not verify_cj_signature(data, signature):
            return jsonify({'error': 'Invalid signature'}), 401
        
        event_type = data.get('event')
        
        if event_type == 'product.stock.updated':
            handle_cj_stock_update(data)
        elif event_type == 'product.price.updated':
            handle_cj_price_update(data)
        elif event_type == 'order.status.updated':
            handle_cj_order_update(data)
        
        return jsonify({'status': 'ok'}), 200
        
    except Exception as e:
        print(f"Erreur webhook CJ: {e}")
        return jsonify({'error': str(e)}), 500

@webhooks_bp.route('/printify', methods=['POST'])
def printify_webhook():
    """Webhook pour Printify"""
    try:
        data = request.json
        
        # Vérifier la signature
        signature = request.headers.get('X-Printify-Signature', '')
        if not verify_printify_signature(data, signature):
            return jsonify({'error': 'Invalid signature'}), 401
        
        event_type = data.get('type')
        
        if event_type == 'order:sent-to-production':
            handle_printify_order_production(data)
        elif event_type == 'order:shipment:created':
            handle_printify_shipment(data)
        
        return jsonify({'status': 'ok'}), 200
        
    except Exception as e:
        print(f"Erreur webhook Printify: {e}")
        return jsonify({'error': str(e)}), 500

@webhooks_bp.route('/amazon', methods=['POST'])
def amazon_webhook():
    """Webhook pour Amazon (si disponible)"""
    # Amazon PA-API ne supporte pas les webhooks
    return jsonify({'error': 'Not supported'}), 404

@webhooks_bp.route('/ebay', methods=['POST'])
def ebay_webhook():
    """Webhook pour eBay"""
    try:
        data = request.json
        
        # eBay utilise des notifications
        notification_type = data.get('notificationType')
        
        if notification_type == 'ItemRevised':
            handle_ebay_item_revised(data)
        elif notification_type == 'ItemEnded':
            handle_ebay_item_ended(data)
        
        return jsonify({'status': 'ok'}), 200
        
    except Exception as e:
        print(f"Erreur webhook eBay: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# HANDLERS CJ DROPSHIPPING
# ============================================================================

def handle_cj_stock_update(data):
    """Gérer la mise à jour de stock CJ"""
    product_id = data.get('productId')
    new_stock = data.get('stock', 0)
    
    # Trouver le produit source
    provider = ApiProvider.query.filter_by(slug='cj-dropshipping').first()
    if not provider:
        return
    
    source = ProductSource.query.filter_by(
        provider_id=provider.id,
        external_product_id=product_id
    ).first()
    
    if source:
        # Mettre à jour le stock
        source.external_stock = new_stock
        source.product.stock = new_stock
        source.last_synced_at = datetime.utcnow()
        source.sync_status = 'synced'
        
        db.session.commit()
        
        print(f"✅ Stock mis à jour pour produit {product_id}: {new_stock}")

def handle_cj_price_update(data):
    """Gérer la mise à jour de prix CJ"""
    product_id = data.get('productId')
    new_price = data.get('price', 0)
    
    provider = ApiProvider.query.filter_by(slug='cj-dropshipping').first()
    if not provider:
        return
    
    source = ProductSource.query.filter_by(
        provider_id=provider.id,
        external_product_id=product_id
    ).first()
    
    if source:
        # Mettre à jour le prix (avec marge)
        from models.api_provider import CategoryMapping
        
        mapping = CategoryMapping.query.filter_by(
            provider_id=provider.id,
            mps_category_id=source.product.category_id
        ).first()
        
        if mapping:
            source.external_price = new_price
            source.product.price = new_price * mapping.apply_markup
            source.last_synced_at = datetime.utcnow()
            
            db.session.commit()
            
            print(f"✅ Prix mis à jour pour produit {product_id}: {new_price}")

def handle_cj_order_update(data):
    """Gérer la mise à jour de commande CJ"""
    order_id = data.get('orderId')
    status = data.get('status')
    tracking = data.get('trackingNumber')
    
    # Mettre à jour la commande MPS correspondante
    from models.order import Order
    
    order = Order.query.filter_by(external_order_id=order_id).first()
    if order:
        # Mapper le statut CJ vers statut MPS
        status_mapping = {
            'processing': 'processing',
            'shipped': 'shipped',
            'delivered': 'delivered',
            'cancelled': 'cancelled'
        }
        
        order.status = status_mapping.get(status, order.status)
        order.tracking_number = tracking
        
        db.session.commit()
        
        print(f"✅ Commande {order_id} mise à jour: {status}")

# ============================================================================
# HANDLERS PRINTIFY
# ============================================================================

def handle_printify_order_production(data):
    """Gérer l'envoi en production Printify"""
    order_id = data.get('resource', {}).get('id')
    
    from models.order import Order
    
    order = Order.query.filter_by(external_order_id=str(order_id)).first()
    if order:
        order.status = 'processing'
        db.session.commit()
        
        print(f"✅ Commande Printify {order_id} en production")

def handle_printify_shipment(data):
    """Gérer l'expédition Printify"""
    order_id = data.get('resource', {}).get('id')
    shipment = data.get('resource', {}).get('shipments', [{}])[0]
    tracking = shipment.get('tracking_number')
    
    from models.order import Order
    
    order = Order.query.filter_by(external_order_id=str(order_id)).first()
    if order:
        order.status = 'shipped'
        order.tracking_number = tracking
        db.session.commit()
        
        print(f"✅ Commande Printify {order_id} expédiée: {tracking}")

# ============================================================================
# HANDLERS EBAY
# ============================================================================

def handle_ebay_item_revised(data):
    """Gérer la révision d'un article eBay"""
    item_id = data.get('itemId')
    
    provider = ApiProvider.query.filter_by(slug='ebay').first()
    if not provider:
        return
    
    source = ProductSource.query.filter_by(
        provider_id=provider.id,
        external_product_id=item_id
    ).first()
    
    if source:
        # Marquer pour resynchronisation
        source.sync_status = 'pending'
        db.session.commit()
        
        print(f"✅ Article eBay {item_id} marqué pour resync")

def handle_ebay_item_ended(data):
    """Gérer la fin d'un article eBay"""
    item_id = data.get('itemId')
    
    provider = ApiProvider.query.filter_by(slug='ebay').first()
    if not provider:
        return
    
    source = ProductSource.query.filter_by(
        provider_id=provider.id,
        external_product_id=item_id
    ).first()
    
    if source:
        # Désactiver le produit
        source.product.is_active = False
        source.is_active = False
        db.session.commit()
        
        print(f"✅ Article eBay {item_id} désactivé")

# ============================================================================
# VÉRIFICATION SIGNATURES
# ============================================================================

def verify_cj_signature(data, signature):
    """Vérifier la signature CJ Dropshipping"""
    # Récupérer le secret du provider
    provider = ApiProvider.query.filter_by(slug='cj-dropshipping').first()
    if not provider:
        return False
    
    # Calculer la signature attendue
    expected = hmac.new(
        provider.api_secret.encode(),
        str(data).encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected)

def verify_printify_signature(data, signature):
    """Vérifier la signature Printify"""
    provider = ApiProvider.query.filter_by(slug='printify').first()
    if not provider:
        return False
    
    # Printify utilise HMAC SHA256
    expected = hmac.new(
        provider.api_key.encode(),
        str(data).encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected)
