"""
Routes pour la gestion de la livraison CJ
Phase 1.2 - Checkout & Livraison
"""
from flask import Blueprint, jsonify, request, session
from services.cj_shipping_service import CjShippingService
from services.api_providers.cj_dropshipping_optimized import CJDropshippingApiOptimized
from config import Config
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('shipping', __name__, url_prefix='/api/shipping')


def get_cj_api():
    """Obtenir une instance de l'API CJ"""
    return CJDropshippingApiOptimized(
        email=Config.CJ_EMAIL,
        password=Config.CJ_PASSWORD,
        dev_key=Config.CJ_DEV_KEY
    )


@bp.route('/methods/<country_code>', methods=['GET'])
def get_shipping_methods(country_code):
    """
    Récupérer les méthodes de livraison disponibles pour un pays
    GET /api/shipping/methods/<country_code>
    """
    try:
        cj_api = get_cj_api()
        shipping_service = CjShippingService(cj_api)
        
        # Optionnel: IDs produits pour filtrer les méthodes
        product_ids = request.args.get('product_ids')
        if product_ids:
            product_ids = [pid.strip() for pid in product_ids.split(',')]
        
        result = shipping_service.get_shipping_methods(country_code, product_ids)
        
        return jsonify(result), 200 if result['success'] else 400
        
    except Exception as e:
        logger.error(f"Erreur get_shipping_methods: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@bp.route('/calculate', methods=['POST'])
def calculate_shipping():
    """
    Calculer les frais de livraison pour un panier
    POST /api/shipping/calculate
    Body: {
        cart_items: [{product_id, variant_id, quantity}],
        country_code: str,
        shipping_method_id: str (optional)
    }
    """
    try:
        data = request.get_json()
        
        cart_items = data.get('cart_items', [])
        country_code = data.get('country_code')
        shipping_method_id = data.get('shipping_method_id')
        
        if not cart_items or not country_code:
            return jsonify({
                'success': False,
                'message': 'cart_items et country_code requis'
            }), 400
        
        cj_api = get_cj_api()
        shipping_service = CjShippingService(cj_api)
        
        result = shipping_service.calculate_shipping_cost(
            cart_items,
            country_code,
            shipping_method_id
        )
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Erreur calculate_shipping: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@bp.route('/estimate-delivery/<country_code>', methods=['GET'])
def estimate_delivery(country_code):
    """
    Estimer le délai de livraison
    GET /api/shipping/estimate-delivery/<country_code>
    """
    try:
        shipping_method_id = request.args.get('method_id')
        
        cj_api = get_cj_api()
        shipping_service = CjShippingService(cj_api)
        
        result = shipping_service.estimate_delivery_time(country_code, shipping_method_id)
        
        return jsonify(result), 200 if result['success'] else 400
        
    except Exception as e:
        logger.error(f"Erreur estimate_delivery: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@bp.route('/validate-address', methods=['POST'])
def validate_address():
    """
    Valider une adresse de livraison
    POST /api/shipping/validate-address
    Body: {
        country: str,
        city: str,
        address: str,
        zip_code: str,
        state: str (optional),
        phone: str (optional)
    }
    """
    try:
        address_data = request.get_json()
        
        if not address_data:
            return jsonify({
                'success': False,
                'message': 'Données adresse requises'
            }), 400
        
        cj_api = get_cj_api()
        shipping_service = CjShippingService(cj_api)
        
        result = shipping_service.validate_shipping_address(address_data)
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Erreur validate_address: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@bp.route('/supported-countries', methods=['GET'])
def get_supported_countries():
    """
    Obtenir la liste des pays supportés
    GET /api/shipping/supported-countries
    """
    try:
        cj_api = get_cj_api()
        shipping_service = CjShippingService(cj_api)
        
        countries = shipping_service.get_supported_countries()
        
        return jsonify({
            'success': True,
            'countries': countries,
            'total': len(countries)
        }), 200
        
    except Exception as e:
        logger.error(f"Erreur get_supported_countries: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@bp.route('/zones', methods=['GET'])
def get_shipping_zones():
    """
    Obtenir les zones de livraison
    GET /api/shipping/zones
    """
    try:
        cj_api = get_cj_api()
        shipping_service = CjShippingService(cj_api)
        
        zones = shipping_service.get_shipping_zones()
        
        return jsonify({
            'success': True,
            'zones': zones
        }), 200
        
    except Exception as e:
        logger.error(f"Erreur get_shipping_zones: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@bp.route('/cart/calculate', methods=['POST'])
def calculate_cart_shipping():
    """
    Calculer les frais de livraison pour le panier en session
    POST /api/shipping/cart/calculate
    Body: {
        country_code: str,
        shipping_method_id: str (optional)
    }
    """
    try:
        data = request.get_json()
        country_code = data.get('country_code')
        
        if not country_code:
            return jsonify({
                'success': False,
                'message': 'country_code requis'
            }), 400
        
        # Récupérer le panier depuis la session
        cart = session.get('cart', {})
        
        if not cart:
            return jsonify({
                'success': False,
                'message': 'Panier vide'
            }), 400
        
        # Convertir le panier en format attendu
        cart_items = []
        for key, item in cart.items():
            cart_items.append({
                'product_id': item.get('product_id'),
                'variant_id': item.get('variant_id'),
                'quantity': item.get('quantity', 1)
            })
        
        cj_api = get_cj_api()
        shipping_service = CjShippingService(cj_api)
        
        shipping_method_id = data.get('shipping_method_id')
        
        result = shipping_service.calculate_shipping_cost(
            cart_items,
            country_code,
            shipping_method_id
        )
        
        # Stocker les frais de livraison dans la session
        if result['success']:
            session['shipping_cost'] = result['shipping_cost']
            session['shipping_method'] = result.get('method')
            session['shipping_country'] = country_code
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Erreur calculate_cart_shipping: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
