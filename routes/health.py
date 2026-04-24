"""
Routes pour health check et métriques
Phase 4 - Monitoring
"""
from flask import Blueprint, jsonify
from services.metrics_service import get_metrics_service

health_bp = Blueprint('health', __name__)


@health_bp.route('/health')
def health_check():
    """Endpoint de health check"""
    metrics = get_metrics_service()
    health = metrics.get_health_status()
    
    status_code = 200 if health['status'] == 'healthy' else 503
    
    return jsonify(health), status_code


@health_bp.route('/metrics')
def metrics():
    """Endpoint de métriques"""
    metrics_service = get_metrics_service()
    
    data = {
        'system': metrics_service.get_system_metrics(),
        'performance': metrics_service.get_performance_metrics()
    }
    
    return jsonify(data)


@health_bp.route('/metrics/sales')
def sales_metrics():
    """Métriques de ventes"""
    metrics_service = get_metrics_service()
    
    data = {
        'last_7_days': metrics_service.get_sales_metrics(7),
        'last_30_days': metrics_service.get_sales_metrics(30),
        'top_products': metrics_service.get_top_products(10)
    }
    
    return jsonify(data)
