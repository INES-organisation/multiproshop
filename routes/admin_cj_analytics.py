"""
Routes admin pour analytics CJ Dropshipping avancées
Dashboard complet avec métriques temps réel
"""
from flask import Blueprint, jsonify, request
from decorators import login_required
from models.product import Product
from models.product_variant import ProductVariant
from models.order import Order
from models.category import Category
from models.webhook_log import WebhookLog
from extensions import db
from sqlalchemy import func, desc
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('admin_cj_analytics', __name__, url_prefix='/admin/api/cj/analytics')


@bp.route('/dashboard', methods=['GET'])
@login_required
def get_dashboard():
    """
    Récupérer les métriques du dashboard CJ
    GET /admin/api/cj/analytics/dashboard
    """
    try:
        # Statistiques produits
        total_products = Product.query.filter(Product.cj_pid.isnot(None)).count()
        active_products = Product.query.filter(
            Product.cj_pid.isnot(None),
            Product.is_active == True
        ).count()
        published_products = Product.query.filter(
            Product.cj_pid.isnot(None),
            Product.published == True
        ).count()
        
        # Statistiques stock
        total_stock = db.session.query(func.sum(Product.stock)).filter(
            Product.cj_pid.isnot(None)
        ).scalar() or 0
        
        low_stock_products = Product.query.filter(
            Product.cj_pid.isnot(None),
            Product.stock < Product.low_stock_threshold,
            Product.stock > 0
        ).count()
        
        out_of_stock_products = Product.query.filter(
            Product.cj_pid.isnot(None),
            Product.stock == 0
        ).count()
        
        # Statistiques variantes
        total_variants = ProductVariant.query.join(Product).filter(
            Product.cj_pid.isnot(None)
        ).count()
        
        # Statistiques commandes CJ
        total_orders = Order.query.filter(Order.cj_order_id.isnot(None)).count()
        
        pending_orders = Order.query.filter(
            Order.cj_order_id.isnot(None),
            Order.status.in_(['paid', 'processing'])
        ).count()
        
        shipped_orders = Order.query.filter(
            Order.cj_order_id.isnot(None),
            Order.status == 'shipped'
        ).count()
        
        delivered_orders = Order.query.filter(
            Order.cj_order_id.isnot(None),
            Order.status == 'delivered'
        ).count()
        
        # Statistiques webhooks (30 derniers jours)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        webhook_stats = db.session.query(
            WebhookLog.event_type,
            func.count(WebhookLog.id).label('count'),
            func.sum(func.case((WebhookLog.status == 'success', 1), else_=0)).label('success'),
            func.sum(func.case((WebhookLog.status == 'error', 1), else_=0)).label('error')
        ).filter(
            WebhookLog.created_at >= thirty_days_ago
        ).group_by(WebhookLog.event_type).all()
        
        webhooks_by_type = {}
        for stat in webhook_stats:
            webhooks_by_type[stat.event_type] = {
                'total': stat.count,
                'success': stat.success,
                'error': stat.error,
                'success_rate': round((stat.success / stat.count * 100) if stat.count > 0 else 0, 2)
            }
        
        # Dernières synchronisations
        last_product_sync = db.session.query(func.max(Product.cj_last_sync)).filter(
            Product.cj_pid.isnot(None)
        ).scalar()
        
        # Produits par catégorie
        products_by_category = db.session.query(
            Category.name,
            func.count(Product.id).label('count')
        ).join(Product).filter(
            Product.cj_pid.isnot(None)
        ).group_by(Category.name).order_by(desc('count')).limit(10).all()
        
        category_distribution = [
            {'category': cat.name, 'count': cat.count}
            for cat in products_by_category
        ]
        
        # Valeur totale du stock
        total_stock_value = db.session.query(
            func.sum(Product.cost_price * Product.stock)
        ).filter(
            Product.cj_pid.isnot(None),
            Product.cost_price.isnot(None)
        ).scalar() or 0
        
        # Valeur potentielle de vente
        potential_revenue = db.session.query(
            func.sum(Product.price * Product.stock)
        ).filter(
            Product.cj_pid.isnot(None),
            Product.price.isnot(None)
        ).scalar() or 0
        
        # Marge potentielle
        potential_margin = potential_revenue - total_stock_value
        margin_percentage = round((potential_margin / total_stock_value * 100) if total_stock_value > 0 else 0, 2)
        
        return jsonify({
            'success': True,
            'data': {
                'products': {
                    'total': total_products,
                    'active': active_products,
                    'published': published_products,
                    'inactive': total_products - active_products
                },
                'stock': {
                    'total_units': int(total_stock),
                    'low_stock': low_stock_products,
                    'out_of_stock': out_of_stock_products,
                    'total_value': round(total_stock_value, 2),
                    'potential_revenue': round(potential_revenue, 2),
                    'potential_margin': round(potential_margin, 2),
                    'margin_percentage': margin_percentage
                },
                'variants': {
                    'total': total_variants,
                    'average_per_product': round(total_variants / total_products, 2) if total_products > 0 else 0
                },
                'orders': {
                    'total': total_orders,
                    'pending': pending_orders,
                    'shipped': shipped_orders,
                    'delivered': delivered_orders
                },
                'webhooks': webhooks_by_type,
                'sync': {
                    'last_product_sync': last_product_sync.isoformat() if last_product_sync else None
                },
                'distribution': {
                    'by_category': category_distribution
                }
            }
        })
        
    except Exception as e:
        logger.error(f"[Admin] Erreur get_dashboard: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@bp.route('/sync-history', methods=['GET'])
@login_required
def get_sync_history():
    """
    Récupérer l'historique des synchronisations
    GET /admin/api/cj/analytics/sync-history?days=30
    """
    try:
        days = int(request.args.get('days', 30))
        start_date = datetime.now() - timedelta(days=days)
        
        # Produits synchronisés par jour
        sync_by_day = db.session.query(
            func.date(Product.cj_last_sync).label('date'),
            func.count(Product.id).label('count')
        ).filter(
            Product.cj_pid.isnot(None),
            Product.cj_last_sync >= start_date
        ).group_by(func.date(Product.cj_last_sync)).order_by('date').all()
        
        history = [
            {'date': str(item.date), 'products_synced': item.count}
            for item in sync_by_day
        ]
        
        return jsonify({
            'success': True,
            'data': {
                'history': history,
                'period_days': days
            }
        })
        
    except Exception as e:
        logger.error(f"[Admin] Erreur get_sync_history: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@bp.route('/top-products', methods=['GET'])
@login_required
def get_top_products():
    """
    Récupérer les produits les plus performants
    GET /admin/api/cj/analytics/top-products?limit=10&sort=sales
    """
    try:
        limit = int(request.args.get('limit', 10))
        sort_by = request.args.get('sort', 'sales')  # sales, views, stock
        
        query = Product.query.filter(Product.cj_pid.isnot(None))
        
        if sort_by == 'sales':
            query = query.order_by(desc(Product.sales_count))
        elif sort_by == 'views':
            query = query.order_by(desc(Product.views_count))
        elif sort_by == 'stock':
            query = query.order_by(desc(Product.stock))
        elif sort_by == 'revenue':
            query = query.order_by(desc(Product.price * Product.sales_count))
        
        products = query.limit(limit).all()
        
        top_products = []
        for product in products:
            revenue = product.price * product.sales_count if product.price and product.sales_count else 0
            cost = product.cost_price * product.sales_count if product.cost_price and product.sales_count else 0
            margin = revenue - cost
            
            top_products.append({
                'id': product.id,
                'name': product.name,
                'cj_pid': product.cj_pid,
                'sales_count': product.sales_count or 0,
                'views_count': product.views_count or 0,
                'stock': product.stock,
                'price': product.price,
                'revenue': round(revenue, 2),
                'margin': round(margin, 2),
                'image_url': product.image_url
            })
        
        return jsonify({
            'success': True,
            'data': {
                'products': top_products,
                'sort_by': sort_by,
                'limit': limit
            }
        })
        
    except Exception as e:
        logger.error(f"[Admin] Erreur get_top_products: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@bp.route('/webhook-logs', methods=['GET'])
@login_required
def get_webhook_logs():
    """
    Récupérer les logs webhooks récents
    GET /admin/api/cj/analytics/webhook-logs?limit=50&status=all
    """
    try:
        limit = int(request.args.get('limit', 50))
        status_filter = request.args.get('status', 'all')  # all, success, error
        
        query = WebhookLog.query
        
        if status_filter != 'all':
            query = query.filter(WebhookLog.status == status_filter)
        
        logs = query.order_by(desc(WebhookLog.created_at)).limit(limit).all()
        
        webhook_logs = []
        for log in logs:
            webhook_logs.append({
                'id': log.id,
                'event_type': log.event_type,
                'status': log.status,
                'message': log.message,
                'error_message': log.error_message,
                'created_at': log.created_at.isoformat() if log.created_at else None
            })
        
        return jsonify({
            'success': True,
            'data': {
                'logs': webhook_logs,
                'limit': limit,
                'status_filter': status_filter
            }
        })
        
    except Exception as e:
        logger.error(f"[Admin] Erreur get_webhook_logs: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@bp.route('/performance', methods=['GET'])
@login_required
def get_performance_metrics():
    """
    Récupérer les métriques de performance CJ
    GET /admin/api/cj/analytics/performance
    """
    try:
        # Taux de conversion (produits vus vs vendus)
        products_with_views = Product.query.filter(
            Product.cj_pid.isnot(None),
            Product.views_count > 0
        ).count()
        
        products_with_sales = Product.query.filter(
            Product.cj_pid.isnot(None),
            Product.sales_count > 0
        ).count()
        
        conversion_rate = round(
            (products_with_sales / products_with_views * 100) if products_with_views > 0 else 0,
            2
        )
        
        # Taux de disponibilité (produits en stock)
        total_products = Product.query.filter(Product.cj_pid.isnot(None)).count()
        out_of_stock_products = Product.query.filter(Product.cj_pid.isnot(None), Product.stock <= 0).count()
        availability_rate = round(
            ((total_products - out_of_stock_products) / total_products * 100) if total_products > 0 else 0,
            2
        )
        
        # Taux de succès webhooks (7 derniers jours)
        seven_days_ago = datetime.now() - timedelta(days=7)
        
        total_webhooks = WebhookLog.query.filter(
            WebhookLog.created_at >= seven_days_ago
        ).count()
        
        successful_webhooks = WebhookLog.query.filter(
            WebhookLog.created_at >= seven_days_ago,
            WebhookLog.status == 'success'
        ).count()
        
        webhook_success_rate = round(
            (successful_webhooks / total_webhooks * 100) if total_webhooks > 0 else 0,
            2
        )
        
        # Temps moyen de synchronisation (estimation)
        avg_sync_time = "< 1 minute"  # Placeholder - à implémenter avec vraies métriques
        
        return jsonify({
            'success': True,
            'data': {
                'conversion_rate': conversion_rate,
                'availability_rate': availability_rate,
                'webhook_success_rate': webhook_success_rate,
                'avg_sync_time': avg_sync_time,
                'products_with_views': products_with_views,
                'products_with_sales': products_with_sales,
                'total_webhooks_7d': total_webhooks,
                'successful_webhooks_7d': successful_webhooks
            }
        })
        
    except Exception as e:
        logger.error(f"[Admin] Erreur get_performance_metrics: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
