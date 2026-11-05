"""
API Routes pour les produits et variantes
Expose les données produits pour le frontend
"""
import re

from flask import Blueprint, jsonify, request, url_for
from sqlalchemy import literal
from models.product import Product
from models.product_variant import ProductVariant
from extensions import db, cache
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


_PROJECT = re.compile(r'^[a-z0-9-]{1,30}$')


def clean_projects(raw):
    """« TonyAlpha, digita ,, x y » → « digita,tonyalpha » : identifiants valides, sans doublon."""
    return ','.join(sorted({p for p in (x.strip().lower() for x in (raw or '').split(',')) if _PROJECT.match(p)}))


@bp.route('/catalog/<project>', methods=['GET'])
@cache.cached(timeout=300, query_string=True)
def catalog(project):
    """Catalogue d'une vitrine (TonyAlpha80, DIGITA, Sérénis…) : produits en ligne marqués pour ce projet
    dans l'admin (champ « Vitrines »). Public, comme les fiches du site. ?page=1&per_page=24&q=mot"""
    if not _PROJECT.match(project):
        return jsonify({'success': False, 'message': 'Projet invalide'}), 400
    page = max(request.args.get('page', 1, type=int), 1)
    per_page = min(max(request.args.get('per_page', 24, type=int), 1), 100)
    q = Product.query.filter(Product.is_active.is_(True),
                             (literal(',') + Product.projects + literal(',')).like(f'%,{project},%'))
    if request.args.get('q'):
        q = q.filter(Product.name.ilike(f"%{request.args['q'][:100]}%"))
    pg = q.order_by(Product.is_featured.desc(), Product.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    resp = jsonify({'success': True, 'project': project, 'page': page, 'total': pg.total, 'products': [{
        'id': p.id, 'name': p.name, 'slug': p.slug, 'short_description': p.short_description,
        'price': p.price, 'compare_price': p.compare_price, 'image_url': p.image_url,
        'images': p.get_images_list(), 'category': p.category.name if p.category else None,
        'in_stock': (p.stock or 0) > 0,
        'url': url_for('products.product_detail', product_id=p.id, _external=True),
    } for p in pg.items]})
    resp.headers['Access-Control-Allow-Origin'] = '*'  # données publiques, lisibles depuis le navigateur des vitrines
    return resp
