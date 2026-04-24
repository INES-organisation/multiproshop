"""
API Routes pour le calcul de livraison CJ Dropshipping
"""
from flask import Blueprint, jsonify, request
from models.product import Product
from services.api_providers.cj_dropshipping_optimized import CJDropshippingApiOptimized
from config import Config
from flask_login import current_user
import logging
import os

logger = logging.getLogger(__name__)

bp = Blueprint('api_shipping', __name__, url_prefix='/api/cj')


@bp.route('/shipping/calculate', methods=['POST'])
def calculate_shipping():
    """
    Calculer les frais de livraison CJ pour un produit
    POST /api/cj/shipping/calculate
    Body: {
        "product_id": int,
        "country": str,
        "quantity": int (optional)
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'Données manquantes'
            }), 400
        
        product_id = data.get('product_id')
        country = data.get('country', 'FR')
        quantity = data.get('quantity', 1)
        
        if not product_id:
            return jsonify({
                'success': False,
                'message': 'product_id requis'
            }), 400
        
        # Récupérer le produit
        product = Product.query.get(product_id)
        
        if not product or not product.cj_pid:
            return jsonify({
                'success': False,
                'message': 'Produit CJ non trouvé'
            }), 404
        
        # Créer l'API CJ avec les credentials
        cj_api = CJDropshippingApiOptimized(
            email=os.getenv('CJ_EMAIL') or Config.CJ_EMAIL,
            password=os.getenv('CJ_PASSWORD') or Config.CJ_PASSWORD
        )
        
        # Calculer les frais de livraison
        # L'API CJ attend une liste de produits
        products_data = [{
            'pid': product.cj_pid,
            'quantity': quantity
        }]
        
        shipping_result = cj_api.calculate_shipping(
            products=products_data,
            country_code=country
        )
        
        if not shipping_result or not shipping_result.get('success'):
            return jsonify({
                'success': False,
                'message': 'Impossible de calculer les frais de livraison',
                'methods': []
            })
        
        # Extraire les méthodes de livraison
        shipping_data = shipping_result.get('data', {})
        methods = []
        
        # Format attendu de CJ API
        if isinstance(shipping_data, list):
            for method in shipping_data:
                methods.append({
                    'name': method.get('shippingName', 'Standard'),
                    'code': method.get('shippingCode', ''),
                    'price': float(method.get('freight', 0)),
                    'delivery_time': method.get('deliveryTime', '15-30 jours'),
                    'description': method.get('description', '')
                })
        
        # Si pas de méthodes, ajouter une méthode par défaut
        if not methods:
            methods.append({
                'name': 'Livraison Standard',
                'code': 'STANDARD',
                'price': 0.0,
                'delivery_time': '15-30 jours',
                'description': 'Livraison gratuite'
            })
        
        return jsonify({
            'success': True,
            'methods': methods,
            'country': country,
            'product_id': product_id
        })
        
    except Exception as e:
        logger.error(f"Erreur calculate_shipping: {e}")
        return jsonify({
            'success': False,
            'message': str(e),
            'methods': []
        }), 500


@bp.route('/shipping/countries', methods=['GET'])
def get_shipping_countries():
    """
    Récupérer la liste des pays supportés pour la livraison
    GET /api/cj/shipping/countries
    """
    try:
        # Liste des principaux pays (à compléter selon CJ API)
        countries = [
            {'code': 'FR', 'name': 'France'},
            {'code': 'US', 'name': 'États-Unis'},
            {'code': 'GB', 'name': 'Royaume-Uni'},
            {'code': 'DE', 'name': 'Allemagne'},
            {'code': 'ES', 'name': 'Espagne'},
            {'code': 'IT', 'name': 'Italie'},
            {'code': 'CA', 'name': 'Canada'},
            {'code': 'AU', 'name': 'Australie'},
            {'code': 'BE', 'name': 'Belgique'},
            {'code': 'NL', 'name': 'Pays-Bas'},
            {'code': 'CH', 'name': 'Suisse'},
            {'code': 'SE', 'name': 'Suède'},
            {'code': 'NO', 'name': 'Norvège'},
            {'code': 'DK', 'name': 'Danemark'},
            {'code': 'FI', 'name': 'Finlande'},
            {'code': 'PL', 'name': 'Pologne'},
            {'code': 'PT', 'name': 'Portugal'},
            {'code': 'AT', 'name': 'Autriche'},
            {'code': 'IE', 'name': 'Irlande'},
            {'code': 'NZ', 'name': 'Nouvelle-Zélande'}
        ]
        
        return jsonify({
            'success': True,
            'countries': countries
        })
        
    except Exception as e:
        logger.error(f"Erreur get_shipping_countries: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
