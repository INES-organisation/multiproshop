"""
API Routes pour les produits et variantes
Expose les données produits pour le frontend
"""
from flask import Blueprint, jsonify, request
from models.product import Product
from models.product_variant import ProductVariant
from extensions import db
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('api_products', __name__, url_prefix='/api')


@bp.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """
    Récupérer les détails d'un produit
    GET /api/products/<id>
    """
    try:
        product = Product.query.get(product_id)
        
        if not product:
            return jsonify({
                'success': False,
                'message': 'Produit non trouvé'
            }), 404
        
        return jsonify({
            'success': True,
            'product': {
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'price': float(product.price) if product.price else 0,
                'compare_price': float(product.compare_price) if product.compare_price else None,
                'stock': product.stock,
                'image_url': product.image_url,
                'images': product.get_images_list() if hasattr(product, 'get_images_list') else [],
                'sku': product.sku,
                'cj_pid': product.cj_pid,
                'weight': product.product_weight,
                'material': product.material,
                'category': {
                    'id': product.category.id,
                    'name': product.category.name
                } if product.category else None
            }
        })
        
    except Exception as e:
        logger.error(f"Erreur get_product: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@bp.route('/products/<int:product_id>/variants', methods=['GET'])
def get_product_variants(product_id):
    """
    Récupérer toutes les variantes d'un produit
    GET /api/products/<id>/variants
    """
    try:
        product = Product.query.get(product_id)
        
        if not product:
            return jsonify({
                'success': False,
                'message': 'Produit non trouvé'
            }), 404
        
        variants = ProductVariant.query.filter_by(product_id=product_id).all()
        
        variants_data = []
        for variant in variants:
            variants_data.append({
                'id': variant.id,
                'cj_vid': variant.cj_vid,
                'variant_key': variant.variant_key,
                'color': variant.color,
                'size': variant.size,
                'price': float(variant.variant_price) if variant.variant_price else float(product.price),
                'stock': variant.variant_stock,
                'image_url': variant.variant_image_url,
                'sku': variant.variant_sku,
                'is_active': variant.is_active
            })
        
        return jsonify({
            'success': True,
            'variants': variants_data,
            'total': len(variants_data)
        })
        
    except Exception as e:
        logger.error(f"Erreur get_product_variants: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@bp.route('/variants/product/<int:product_id>/summary', methods=['GET'])
def get_variants_summary(product_id):
    """
    Récupérer un résumé des variantes (couleurs, tailles disponibles)
    GET /api/variants/product/<id>/summary
    """
    try:
        product = Product.query.get(product_id)
        
        if not product:
            return jsonify({
                'success': False,
                'message': 'Produit non trouvé'
            }), 404
        
        variants = ProductVariant.query.filter_by(
            product_id=product_id,
            is_active=True
        ).all()
        
        # Extraire couleurs et tailles uniques
        colors = list(set([v.color for v in variants if v.color]))
        sizes = list(set([v.size for v in variants if v.size]))
        
        # Trier
        colors.sort()
        sizes.sort()
        
        # Préparer les données des variantes
        variants_data = []
        for variant in variants:
            variants_data.append({
                'id': variant.id,
                'color': variant.color,
                'size': variant.size,
                'price': float(variant.variant_price) if variant.variant_price else float(product.price),
                'stock': variant.variant_stock,
                'image_url': variant.variant_image_url
            })
        
        return jsonify({
            'success': True,
            'summary': {
                'has_variants': len(variants) > 0,
                'total_variants': len(variants),
                'colors': colors,
                'sizes': sizes,
                'variants': variants_data,
                'base_price': float(product.price) if product.price else 0,
                'total_stock': sum([v.variant_stock for v in variants]) if variants else product.stock
            }
        })
        
    except Exception as e:
        logger.error(f"Erreur get_variants_summary: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@bp.route('/variants/<int:variant_id>', methods=['GET'])
def get_variant(variant_id):
    """
    Récupérer les détails d'une variante
    GET /api/variants/<id>
    """
    try:
        variant = ProductVariant.query.get(variant_id)
        
        if not variant:
            return jsonify({
                'success': False,
                'message': 'Variante non trouvée'
            }), 404
        
        return jsonify({
            'success': True,
            'variant': {
                'id': variant.id,
                'product_id': variant.product_id,
                'cj_vid': variant.cj_vid,
                'variant_key': variant.variant_key,
                'color': variant.color,
                'size': variant.size,
                'price': float(variant.variant_price) if variant.variant_price else None,
                'stock': variant.variant_stock,
                'image_url': variant.variant_image_url,
                'sku': variant.variant_sku,
                'weight': variant.variant_weight,
                'is_active': variant.is_active
            }
        })
        
    except Exception as e:
        logger.error(f"Erreur get_variant: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
