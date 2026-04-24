"""
Prometheus Exporter pour métriques
Phase 4 - Monitoring avancé Prometheus
"""
from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST
from flask import Response
from functools import wraps
import time
from models.product import Product
from models.order import Order
from models.user import User
from extensions import db


# Métriques Prometheus
http_requests_total = Counter(
    'http_requests_total',
    'Total des requêtes HTTP',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'Durée des requêtes HTTP en secondes',
    ['method', 'endpoint']
)

products_total = Gauge(
    'products_total',
    'Nombre total de produits'
)

products_active = Gauge(
    'products_active',
    'Nombre de produits actifs'
)

products_out_of_stock = Gauge(
    'products_out_of_stock',
    'Nombre de produits en rupture de stock'
)

orders_total = Gauge(
    'orders_total',
    'Nombre total de commandes'
)

orders_pending = Gauge(
    'orders_pending',
    'Nombre de commandes en attente'
)

orders_completed = Gauge(
    'orders_completed',
    'Nombre de commandes complétées'
)

users_total = Gauge(
    'users_total',
    'Nombre total d\'utilisateurs'
)

database_query_duration_seconds = Histogram(
    'database_query_duration_seconds',
    'Durée des requêtes base de données en secondes',
    ['query_type']
)

cache_hits_total = Counter(
    'cache_hits_total',
    'Nombre total de hits cache',
    ['cache_type']
)

cache_misses_total = Counter(
    'cache_misses_total',
    'Nombre total de misses cache',
    ['cache_type']
)

cj_api_requests_total = Counter(
    'cj_api_requests_total',
    'Nombre total d\'appels API CJ',
    ['endpoint', 'status']
)

cj_api_request_duration_seconds = Histogram(
    'cj_api_request_duration_seconds',
    'Durée des appels API CJ en secondes',
    ['endpoint']
)


def track_request(f):
    """Décorateur pour tracker les requêtes HTTP"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import request
        
        start_time = time.time()
        
        try:
            response = f(*args, **kwargs)
            status = response.status_code if hasattr(response, 'status_code') else 200
            
            # Incrémenter compteur
            http_requests_total.labels(
                method=request.method,
                endpoint=request.endpoint or 'unknown',
                status=status
            ).inc()
            
            # Enregistrer durée
            duration = time.time() - start_time
            http_request_duration_seconds.labels(
                method=request.method,
                endpoint=request.endpoint or 'unknown'
            ).observe(duration)
            
            return response
            
        except Exception as e:
            # Incrémenter compteur erreur
            http_requests_total.labels(
                method=request.method,
                endpoint=request.endpoint or 'unknown',
                status=500
            ).inc()
            raise
    
    return decorated_function


def track_database_query(query_type):
    """Décorateur pour tracker les requêtes database"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = f(*args, **kwargs)
                duration = time.time() - start_time
                
                database_query_duration_seconds.labels(
                    query_type=query_type
                ).observe(duration)
                
                return result
            except Exception as e:
                raise
        
        return decorated_function
    return decorator


def track_cache(cache_type):
    """Tracker les hits/misses cache"""
    def hit():
        cache_hits_total.labels(cache_type=cache_type).inc()
    
    def miss():
        cache_misses_total.labels(cache_type=cache_type).inc()
    
    return hit, miss


def track_cj_api_call(endpoint):
    """Décorateur pour tracker les appels API CJ"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = f(*args, **kwargs)
                duration = time.time() - start_time
                
                # Déterminer le statut
                status = 'success'
                if isinstance(result, dict):
                    if not result.get('success', True):
                        status = 'error'
                
                cj_api_requests_total.labels(
                    endpoint=endpoint,
                    status=status
                ).inc()
                
                cj_api_request_duration_seconds.labels(
                    endpoint=endpoint
                ).observe(duration)
                
                return result
            except Exception as e:
                cj_api_requests_total.labels(
                    endpoint=endpoint,
                    status='error'
                ).inc()
                raise
        
        return decorated_function
    return decorator


def update_gauges():
    """Mettre à jour les gauges avec les valeurs actuelles"""
    try:
        # Produits
        total = Product.query.count()
        active = Product.query.filter(Product.is_active == True).count()
        out_of_stock = Product.query.filter(Product.stock_quantity == 0).count()
        
        products_total.set(total)
        products_active.set(active)
        products_out_of_stock.set(out_of_stock)
        
        # Commandes
        total_orders = Order.query.count()
        pending = Order.query.filter(Order.status == 'pending').count()
        completed = Order.query.filter(Order.status == 'completed').count()
        
        orders_total.set(total_orders)
        orders_pending.set(pending)
        orders_completed.set(completed)
        
        # Utilisateurs
        total_users = User.query.count()
        users_total.set(total_users)
        
    except Exception as e:
        print(f"Erreur mise à jour gauges Prometheus: {e}")


def metrics_endpoint():
    """Endpoint pour exposer les métriques Prometheus"""
    # Mettre à jour les gauges avant d'exposer
    update_gauges()
    
    # Générer les métriques
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


class PrometheusExporter:
    """Classe pour gérer l'export Prometheus"""
    
    @staticmethod
    def init_app(app):
        """Initialiser l'exporter avec l'application Flask"""
        
        # Ajouter l'endpoint metrics
        @app.route('/prometheus/metrics')
        def prometheus_metrics():
            return metrics_endpoint()
        
        # Mettre à jour les gauges au démarrage
        with app.app_context():
            update_gauges()
    
    @staticmethod
    def track_request(f):
        """Décorateur pour tracker les requêtes"""
        return track_request(f)
    
    @staticmethod
    def track_database_query(query_type):
        """Décorateur pour tracker les requêtes DB"""
        return track_database_query(query_type)
    
    @staticmethod
    def track_cache(cache_type):
        """Tracker cache"""
        return track_cache(cache_type)
    
    @staticmethod
    def track_cj_api_call(endpoint):
        """Décorateur pour tracker API CJ"""
        return track_cj_api_call(endpoint)
