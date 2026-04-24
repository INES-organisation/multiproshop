"""
Routes API pour le calcul des frais de livraison
"""
from flask import Blueprint, jsonify, request
from services.shipping_service import ShippingService
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('shipping_api', __name__, url_prefix='/api/shipping')


@bp.route('/calculate', methods=['POST'])
def calculate_shipping():
    """
    Calculer les frais de livraison pour un panier
    POST /api/shipping/calculate
    Body: {
        items: [
            {cj_pid: str, cj_vid: str, quantity: int, product: {}}
        ],
        country: str (default: 'FR')
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'items' not in data:
            return jsonify({
                'success': False,
                'error': 'Items requis'
            }), 400
        
        items = data['items']
        country = data.get('country', 'FR')
        
        shipping_service = ShippingService()
        result = shipping_service.calculate_shipping(items, country)
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"[API Shipping] Erreur calculate: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/calculate/product/<int:product_id>', methods=['POST'])
def calculate_product_shipping(product_id):
    """
    Calculer les frais de livraison pour un produit
    POST /api/shipping/calculate/product/<product_id>
    Body: {quantity: int, country: str}
    """
    try:
        data = request.get_json() or {}
        quantity = data.get('quantity', 1)
        country = data.get('country', 'FR')
        
        shipping_service = ShippingService()
        result = shipping_service.calculate_shipping_for_product(
            product_id, quantity, country
        )
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"[API Shipping] Erreur calculate_product: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/methods', methods=['GET'])
def get_shipping_methods():
    """
    Obtenir les méthodes de livraison disponibles
    GET /api/shipping/methods?country=FR
    """
    try:
        country = request.args.get('country', 'FR')
        
        shipping_service = ShippingService()
        
        # Retourner les méthodes par défaut
        methods = shipping_service._get_fallback_methods([], country)
        
        return jsonify({
            'success': True,
            'methods': methods,
            'country': country
        }), 200
        
    except Exception as e:
        logger.error(f"[API Shipping] Erreur get_methods: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
