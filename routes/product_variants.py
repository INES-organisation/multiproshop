"""
Routes API pour la gestion des variantes de produits
"""
from flask import Blueprint, jsonify, request
from services.variant_service import VariantService
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('product_variants', __name__, url_prefix='/api/variants')
variant_service = VariantService()


@bp.route('/product/<int:product_id>', methods=['GET'])
def get_product_variants(product_id):
    """
    Récupérer toutes les variantes d'un produit
    GET /api/variants/product/<product_id>
    """
    try:
        variants = variant_service.get_product_variants(product_id)
        
        return jsonify({
            'success': True,
            'variants': variants,
            'count': len(variants)
        }), 200
        
    except Exception as e:
        logger.error(f"[API Variants] Erreur get_product_variants: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@bp.route('/product/<int:product_id>/summary', methods=['GET'])
def get_product_variants_summary(product_id):
    """
    Récupérer le résumé des variantes d'un produit
    GET /api/variants/product/<product_id>/summary
    """
    try:
        summary = variant_service.get_product_variants_summary(product_id)
        
        return jsonify({
            'success': True,
            'summary': summary
        }), 200
        
    except Exception as e:
        logger.error(f"[API Variants] Erreur get_product_variants_summary: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@bp.route('/<int:variant_id>', methods=['GET'])
def get_variant(variant_id):
    """
    Récupérer une variante par son ID
    GET /api/variants/<variant_id>
    """
    try:
        variant = variant_service.get_variant_by_id(variant_id)
        
        if not variant:
            return jsonify({
                'success': False,
                'message': 'Variante introuvable'
            }), 404
        
        return jsonify({
            'success': True,
            'variant': variant
        }), 200
        
    except Exception as e:
        logger.error(f"[API Variants] Erreur get_variant: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@bp.route('/product/<int:product_id>/colors', methods=['GET'])
def get_available_colors(product_id):
    """
    Récupérer les couleurs disponibles pour un produit
    GET /api/variants/product/<product_id>/colors
    """
    try:
        colors = variant_service.get_available_colors(product_id)
        
        return jsonify({
            'success': True,
            'colors': colors,
            'count': len(colors)
        }), 200
        
    except Exception as e:
        logger.error(f"[API Variants] Erreur get_available_colors: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@bp.route('/product/<int:product_id>/sizes', methods=['GET'])
def get_available_sizes(product_id):
    """
    Récupérer les tailles disponibles pour un produit
    Optionnellement filtré par couleur via query param ?color=
    GET /api/variants/product/<product_id>/sizes?color=White
    """
    try:
        color = request.args.get('color')
        sizes = variant_service.get_available_sizes(product_id, color)
        
        return jsonify({
            'success': True,
            'sizes': sizes,
            'count': len(sizes),
            'filtered_by_color': color
        }), 200
        
    except Exception as e:
        logger.error(f"[API Variants] Erreur get_available_sizes: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@bp.route('/product/<int:product_id>/find', methods=['POST'])
def find_variant_by_options(product_id):
    """
    Trouver une variante par ses options (couleur, taille)
    POST /api/variants/product/<product_id>/find
    Body: {"color": "White", "size": "M"}
    """
    try:
        data = request.get_json()
        color = data.get('color')
        size = data.get('size')
        
        variant = variant_service.get_variant_by_options(product_id, color, size)
        
        if not variant:
            return jsonify({
                'success': False,
                'message': 'Variante introuvable pour ces options'
            }), 404
        
        return jsonify({
            'success': True,
            'variant': variant
        }), 200
        
    except Exception as e:
        logger.error(f"[API Variants] Erreur find_variant_by_options: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@bp.route('/<int:variant_id>/check-availability', methods=['POST'])
def check_variant_availability(variant_id):
    """
    Vérifier la disponibilité d'une variante
    POST /api/variants/<variant_id>/check-availability
    Body: {"quantity": 2}
    """
    try:
        data = request.get_json()
        quantity = data.get('quantity', 1)
        
        available, message = variant_service.check_variant_availability(variant_id, quantity)
        
        return jsonify({
            'success': True,
            'available': available,
            'message': message,
            'stock': variant_service.get_variant_stock(variant_id)
        }), 200
        
    except Exception as e:
        logger.error(f"[API Variants] Erreur check_variant_availability: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@bp.route('/<int:variant_id>/stock', methods=['GET'])
def get_variant_stock(variant_id):
    """
    Récupérer le stock d'une variante
    GET /api/variants/<variant_id>/stock
    """
    try:
        stock = variant_service.get_variant_stock(variant_id)
        
        return jsonify({
            'success': True,
            'variant_id': variant_id,
            'stock': stock,
            'in_stock': stock > 0
        }), 200
        
    except Exception as e:
        logger.error(f"[API Variants] Erreur get_variant_stock: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
