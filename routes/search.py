"""
Routes pour la recherche de produits
Phase 3.2 - Recherche avancée avec filtres
"""
from flask import Blueprint, render_template, request, jsonify
from services.search_service import get_search_service
import logging

logger = logging.getLogger(__name__)

search_bp = Blueprint('search', __name__, url_prefix='/search')


@search_bp.route('/')
def search():
    """Page de résultats de recherche"""
    try:
        query = request.args.get('q', '')
        category_id = request.args.get('category', type=int)
        min_price = request.args.get('min_price', type=float)
        max_price = request.args.get('max_price', type=float)
        in_stock = request.args.get('in_stock', 'false').lower() == 'true'
        sort_by = request.args.get('sort', 'relevance')
        page = request.args.get('page', 1, type=int)
        
        search_service = get_search_service()
        
        # Rechercher
        results = search_service.search_products(
            query=query,
            category_id=category_id,
            min_price=min_price,
            max_price=max_price,
            in_stock_only=in_stock,
            sort_by=sort_by,
            page=page,
            per_page=20
        )
        
        # Récupérer les facettes
        facets = search_service.get_facets(query=query, category_id=category_id)
        
        return render_template(
            'pages/search_results.html',
            query=query,
            results=results,
            facets=facets,
            filters={
                'category_id': category_id,
                'min_price': min_price,
                'max_price': max_price,
                'in_stock': in_stock,
                'sort_by': sort_by
            }
        )
        
    except Exception as e:
        logger.error(f"Erreur recherche: {e}")
        return render_template(
            'pages/search_results.html',
            query='',
            results={'success': False, 'products': [], 'total': 0},
            facets={'success': False},
            error=str(e)
        )


@search_bp.route('/api/suggestions')
def api_suggestions():
    """API: Suggestions de recherche"""
    try:
        query = request.args.get('q', '')
        limit = request.args.get('limit', 5, type=int)
        
        search_service = get_search_service()
        suggestions = search_service.get_search_suggestions(query, limit)
        
        return jsonify({
            'success': True,
            'suggestions': suggestions
        })
        
    except Exception as e:
        logger.error(f"Erreur suggestions: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@search_bp.route('/api/popular')
def api_popular():
    """API: Recherches populaires"""
    try:
        limit = request.args.get('limit', 10, type=int)
        
        search_service = get_search_service()
        popular = search_service.get_popular_searches(limit)
        
        return jsonify({
            'success': True,
            'popular': popular
        })
        
    except Exception as e:
        logger.error(f"Erreur recherches populaires: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
