"""
Utilitaires de cache avancés pour MultiProShop
"""
from functools import wraps
from flask import request
from extensions import cache


def make_cache_key(*args, **kwargs):
    """Générer une clé de cache unique basée sur la requête"""
    path = request.path
    args_str = str(request.args)
    return f"{path}:{args_str}"


def cached_query(timeout=300, key_prefix='query'):
    """
    Décorateur pour cacher les résultats de requêtes DB
    
    Usage:
        @cached_query(timeout=600, key_prefix='products')
        def get_products():
            return Product.query.all()
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Générer clé de cache
            cache_key = f"{key_prefix}:{f.__name__}:{str(args)}:{str(kwargs)}"
            
            # Vérifier cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Exécuter fonction et cacher résultat
            result = f(*args, **kwargs)
            cache.set(cache_key, result, timeout=timeout)
            return result
        
        return decorated_function
    return decorator


def invalidate_cache(key_prefix):
    """
    Invalider le cache pour un préfixe donné
    
    Usage:
        invalidate_cache('products')
    """
    # Note: SimpleCache ne supporte pas la suppression par préfixe
    # Pour Redis, on pourrait faire : cache.delete_many(f"{key_prefix}:*")
    cache.clear()


def cache_page(timeout=300):
    """
    Décorateur pour cacher une page entière
    
    Usage:
        @app.route('/products')
        @cache_page(timeout=600)
        def products():
            return render_template('products.html')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            cache_key = make_cache_key()
            
            # Vérifier cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Exécuter fonction et cacher résultat
            result = f(*args, **kwargs)
            cache.set(cache_key, result, timeout=timeout)
            return result
        
        return decorated_function
    return decorator


class CacheManager:
    """Gestionnaire de cache centralisé"""
    
    # Durées de cache par type
    TIMEOUTS = {
        'page': 300,           # 5 minutes
        'query': 600,          # 10 minutes
        'product': 1800,       # 30 minutes
        'category': 3600,      # 1 heure
        'user': 900,           # 15 minutes
        'static': 86400,       # 24 heures
    }
    
    @staticmethod
    def get_timeout(cache_type='page'):
        """Obtenir le timeout pour un type de cache"""
        return CacheManager.TIMEOUTS.get(cache_type, 300)
    
    @staticmethod
    def cache_product(product_id, data, timeout=None):
        """Cacher un produit"""
        if timeout is None:
            timeout = CacheManager.get_timeout('product')
        cache.set(f'product:{product_id}', data, timeout=timeout)
    
    @staticmethod
    def get_product(product_id):
        """Récupérer un produit du cache"""
        return cache.get(f'product:{product_id}')
    
    @staticmethod
    def cache_category(category_id, data, timeout=None):
        """Cacher une catégorie"""
        if timeout is None:
            timeout = CacheManager.get_timeout('category')
        cache.set(f'category:{category_id}', data, timeout=timeout)
    
    @staticmethod
    def get_category(category_id):
        """Récupérer une catégorie du cache"""
        return cache.get(f'category:{category_id}')
    
    @staticmethod
    def invalidate_product(product_id):
        """Invalider le cache d'un produit"""
        cache.delete(f'product:{product_id}')
    
    @staticmethod
    def invalidate_category(category_id):
        """Invalider le cache d'une catégorie"""
        cache.delete(f'category:{category_id}')
    
    @staticmethod
    def clear_all():
        """Vider tout le cache"""
        cache.clear()
