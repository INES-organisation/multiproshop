"""
API Routes pour les avis produits CJ Dropshipping
"""
from flask import Blueprint, jsonify
from models.product import Product
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('api_reviews', __name__, url_prefix='/api/cj')


@bp.route('/products/<cj_pid>/reviews', methods=['GET'])
def get_product_reviews(cj_pid):
    """
    Avis affichables d'un produit (déposés sur le site, approuvés)
    GET /api/cj/products/<cj_pid>/reviews
    Les avis CJ (laissés sur d'autres boutiques) et les avis d'exemple ne sont jamais renvoyés.
    """
    product = Product.query.filter_by(cj_pid=cj_pid).first()
    reviews = product.latest_reviews if product else []
    return jsonify({
        'success': True,
        'reviews': [{
            'id': r.id,
            'author': r.author_name,
            'rating': r.rating,
            'comment': r.comment,
            'date': r.created_at.isoformat() if r.created_at else '',
            'verified': bool(r.verified_purchase),
        } for r in reviews],
        'average': product.average_rating if product else 0,
        'total': product.reviews_count if product else 0,
        'source': 'site'
    })
