"""
Routes pour le dashboard CJ Dropshipping Admin
Phase 2.2 - Interface de monitoring et analytics
"""
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required
from functools import wraps
from models.user import User
from services.cj_analytics_service import CjAnalyticsService
import logging

logger = logging.getLogger(__name__)

admin_cj_dashboard = Blueprint('admin_cj_dashboard', __name__, url_prefix='/admin/cj')


def admin_required(f):
    """Décorateur pour vérifier que l'utilisateur est admin"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        from flask_login import current_user
        if not current_user.is_admin:
            return jsonify({'error': 'Accès non autorisé'}), 403
        return f(*args, **kwargs)
    return decorated_function


@admin_cj_dashboard.route('/dashboard')
@admin_required
def dashboard():
    """Page principale du dashboard CJ"""
    try:
        analytics = CjAnalyticsService()
        
        # Récupérer la période (défaut: 30 jours)
        days = request.args.get('days', 30, type=int)
        
        # KPIs principaux
        kpis = analytics.get_dashboard_kpis(days=days)
        
        # Alertes
        alerts = analytics.get_alerts()
        
        # Stats produits
        product_stats = analytics.get_product_stats()
        
        return render_template(
            'admin/cj_dashboard.html',
            kpis=kpis,
            alerts=alerts,
            product_stats=product_stats,
            period_days=days
        )
        
    except Exception as e:
        logger.error(f"Erreur dashboard CJ: {e}")
        return render_template(
            'admin/cj_dashboard.html',
            error=str(e)
        )


@admin_cj_dashboard.route('/api/kpis')
@admin_required
def api_kpis():
    """API: Récupérer les KPIs"""
    try:
        days = request.args.get('days', 30, type=int)
        analytics = CjAnalyticsService()
        kpis = analytics.get_dashboard_kpis(days=days)
        return jsonify(kpis)
    except Exception as e:
        logger.error(f"Erreur API KPIs: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_cj_dashboard.route('/api/sales-evolution')
@admin_required
def api_sales_evolution():
    """API: Récupérer l'évolution des ventes"""
    try:
        days = request.args.get('days', 30, type=int)
        analytics = CjAnalyticsService()
        evolution = analytics.get_sales_evolution(days=days)
        return jsonify(evolution)
    except Exception as e:
        logger.error(f"Erreur API évolution ventes: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_cj_dashboard.route('/api/top-products')
@admin_required
def api_top_products():
    """API: Récupérer les produits les plus vendus"""
    try:
        limit = request.args.get('limit', 10, type=int)
        days = request.args.get('days', 30, type=int)
        analytics = CjAnalyticsService()
        top_products = analytics.get_top_products(limit=limit, days=days)
        return jsonify(top_products)
    except Exception as e:
        logger.error(f"Erreur API top produits: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_cj_dashboard.route('/api/category-stats')
@admin_required
def api_category_stats():
    """API: Récupérer les stats par catégorie"""
    try:
        days = request.args.get('days', 30, type=int)
        analytics = CjAnalyticsService()
        stats = analytics.get_category_stats(days=days)
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Erreur API stats catégories: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_cj_dashboard.route('/api/alerts')
@admin_required
def api_alerts():
    """API: Récupérer les alertes"""
    try:
        analytics = CjAnalyticsService()
        alerts = analytics.get_alerts()
        return jsonify(alerts)
    except Exception as e:
        logger.error(f"Erreur API alertes: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_cj_dashboard.route('/api/product-stats')
@admin_required
def api_product_stats():
    """API: Récupérer les stats produits"""
    try:
        analytics = CjAnalyticsService()
        stats = analytics.get_product_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Erreur API stats produits: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
