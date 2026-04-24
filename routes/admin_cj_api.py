"""
Routes API supplémentaires pour l'interface admin CJ (catégories et pricing)
"""
from flask import Blueprint, jsonify, request
from flask_login import login_required
from services.pricing_service import PricingService
from models.category import Category
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('admin_cj_api', __name__, url_prefix='/admin/api/cj')
pricing_service = PricingService()


@bp.route('/category/mapping', methods=['GET'])
@login_required
def get_category_mapping():
    """
    Récupérer le mapping d'une catégorie CJ vers MPS
    GET /admin/api/cj/category/mapping?category_id=xxx
    """
    try:
        from models.api_provider import CategoryMapping, ApiProvider
        
        category_id = request.args.get('category_id')
        if not category_id:
            return jsonify({
                'success': False,
                'message': 'category_id requis'
            }), 400
        
        # Récupérer le provider CJ
        provider = ApiProvider.query.filter_by(slug='cj-dropshipping').first()
        if not provider:
            return jsonify({
                'success': False,
                'message': 'Provider CJ non trouvé'
            }), 404
        
        # Récupérer le mapping
        mapping = CategoryMapping.query.filter_by(
            provider_id=provider.id,
            external_category_id=category_id
        ).first()
        
        if not mapping:
            return jsonify({
                'success': True,
                'mapping': None
            }), 200
        
        # Récupérer la catégorie MPS
        mps_category = Category.query.get(mapping.mps_category_id)
        
        return jsonify({
            'success': True,
            'mapping': {
                'id': mapping.id,
                'mps_category_id': mapping.mps_category_id,
                'mps_category_name': mps_category.name if mps_category else 'Inconnue',
                'apply_markup': mapping.apply_markup,
                'auto_import': mapping.auto_import
            }
        }), 200
        
    except Exception as e:
        logger.error(f"[Admin] Erreur get_category_mapping: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@bp.route('/categories/all', methods=['GET'])
@login_required
def get_all_categories():
    """
    Récupérer toutes les catégories CJ pour la configuration des marges
    GET /admin/api/cj/categories/all
    """
    try:
        categories = Category.query.filter(
            Category.cj_category_id.isnot(None)
        ).order_by(Category.level, Category.name).all()
        
        categories_data = [{
            'id': cat.id,
            'name': cat.name,
            'name_fr': cat.name_fr,
            'level': cat.level,
            'product_count': cat.product_count or 0,
            'cj_category_id': cat.cj_category_id
        } for cat in categories]
        
        return jsonify({
            'success': True,
            'categories': categories_data
        }), 200
        
    except Exception as e:
        logger.error(f"[Admin] Erreur get_all_categories: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@bp.route('/pricing/analytics', methods=['GET'])
@login_required
def get_pricing_analytics():
    """
    Récupérer les analytics de tarification
    GET /admin/api/cj/pricing/analytics
    """
    try:
        analytics = pricing_service.get_pricing_analytics()
        
        return jsonify({
            'success': True,
            'analytics': analytics
        }), 200
        
    except Exception as e:
        logger.error(f"[Admin] Erreur get_pricing_analytics: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@bp.route('/pricing/save-markups', methods=['POST'])
@login_required
def save_markups():
    """
    Enregistrer les marges configurées
    POST /admin/api/cj/pricing/save-markups
    """
    try:
        data = request.get_json()
        
        default_markup = data.get('default_markup', 60)
        category_markups = data.get('category_markups', {})
        
        # Mettre à jour le service
        pricing_service.default_markup = float(default_markup)
        
        for category_name, markup in category_markups.items():
            pricing_service.set_category_markup(category_name, float(markup))
        
        return jsonify({
            'success': True,
            'message': 'Marges enregistrées avec succès'
        }), 200
        
    except Exception as e:
        logger.error(f"[Admin] Erreur save_markups: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@bp.route('/pricing/recalculate', methods=['POST'])
@login_required
def recalculate_prices():
    """
    Recalculer tous les prix des produits par lots pour éviter les locks SQLite
    POST /admin/api/cj/pricing/recalculate
    """
    try:
        from models.product import Product
        from extensions import db
        import time
        
        # Compter le total
        total = Product.query.filter(Product.cj_pid.isnot(None)).count()
        updated = 0
        batch_size = 20  # Petits lots pour éviter les locks
        offset = 0
        
        while offset < total:
            try:
                # Récupérer un lot de produits
                products = Product.query.filter(
                    Product.cj_pid.isnot(None)
                ).offset(offset).limit(batch_size).all()
                
                if not products:
                    break
                
                # Traiter chaque produit du lot
                for product in products:
                    try:
                        # Si cost_price est None, utiliser le prix actuel comme coût
                        if product.cost_price is None and product.price:
                            product.cost_price = product.price
                        
                        # Si on a un cost_price, recalculer le prix de vente
                        if product.cost_price and product.cost_price > 0:
                            # Récupérer la catégorie pour la marge
                            category = Category.query.filter_by(id=product.category_id).first() if product.category_id else None
                            
                            if category:
                                # Mettre à jour avec le pricing service
                                product = pricing_service.update_product_pricing(
                                    product,
                                    product.cost_price,
                                    product.suggested_price
                                )
                                updated += 1
                                
                    except Exception as e:
                        logger.error(f"Erreur produit {product.id}: {e}")
                        continue
                
                # Commit le lot
                db.session.commit()
                
                # Petit délai pour libérer le lock
                time.sleep(0.05)
                
                offset += batch_size
                
            except Exception as e:
                logger.error(f"Erreur lot offset {offset}: {e}")
                db.session.rollback()
                offset += batch_size
                time.sleep(0.1)
                continue
        
        return jsonify({
            'success': True,
            'total': total,
            'updated': updated,
            'message': f'{updated} produits mis à jour sur {total}'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"[Admin] Erreur recalculate_prices: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
