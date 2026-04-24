"""
Service de cache optimisé pour CJ Dropshipping
Utilise Redis pour améliorer les performances
"""
from extensions import cache
from functools import wraps
import logging

logger = logging.getLogger(__name__)


def cache_cj_data(timeout=3600, key_prefix='cj'):
    """
    Décorateur pour cacher les données CJ
    
    Args:
        timeout: Durée du cache en secondes (défaut: 1 heure)
        key_prefix: Préfixe de la clé de cache
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Générer une clé unique basée sur les arguments
            cache_key = f"{key_prefix}:{f.__name__}:{str(args)}:{str(kwargs)}"
            
            # Essayer de récupérer depuis le cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"[Cache] HIT: {cache_key}")
                return cached_result
            
            # Exécuter la fonction et cacher le résultat
            logger.debug(f"[Cache] MISS: {cache_key}")
            result = f(*args, **kwargs)
            
            if result is not None:
                cache.set(cache_key, result, timeout=timeout)
            
            return result
        
        return decorated_function
    return decorator


class CacheService:
    """Service de gestion du cache CJ"""
    
    # Durées de cache recommandées
    CACHE_DURATIONS = {
        'categories': 3600,      # 1 heure
        'products': 1800,        # 30 minutes
        'product_detail': 900,   # 15 minutes
        'shipping': 300,         # 5 minutes
        'reviews': 1800,         # 30 minutes
        'token': 1209600,        # 14 jours
    }
    
    @staticmethod
    def get_categories():
        """Récupérer les catégories depuis le cache"""
        return cache.get('cj:categories')
    
    @staticmethod
    def set_categories(categories, timeout=None):
        """Stocker les catégories en cache"""
        timeout = timeout or CacheService.CACHE_DURATIONS['categories']
        cache.set('cj:categories', categories, timeout=timeout)
        logger.info(f"[Cache] Catégories cachées pour {timeout}s")
    
    @staticmethod
    def get_products(category_id):
        """Récupérer les produits d'une catégorie depuis le cache"""
        return cache.get(f'cj:products:{category_id}')
    
    @staticmethod
    def set_products(category_id, products, timeout=None):
        """Stocker les produits en cache"""
        timeout = timeout or CacheService.CACHE_DURATIONS['products']
        cache.set(f'cj:products:{category_id}', products, timeout=timeout)
        logger.info(f"[Cache] Produits catégorie {category_id} cachés pour {timeout}s")
    
    @staticmethod
    def get_product_detail(product_id):
        """Récupérer les détails d'un produit depuis le cache"""
        return cache.get(f'cj:product:{product_id}')
    
    @staticmethod
    def set_product_detail(product_id, product, timeout=None):
        """Stocker les détails d'un produit en cache"""
        timeout = timeout or CacheService.CACHE_DURATIONS['product_detail']
        cache.set(f'cj:product:{product_id}', product, timeout=timeout)
    
    @staticmethod
    def get_shipping(cart_hash, country):
        """Récupérer les frais de livraison depuis le cache"""
        return cache.get(f'cj:shipping:{cart_hash}:{country}')
    
    @staticmethod
    def set_shipping(cart_hash, country, shipping_data, timeout=None):
        """Stocker les frais de livraison en cache"""
        timeout = timeout or CacheService.CACHE_DURATIONS['shipping']
        cache.set(f'cj:shipping:{cart_hash}:{country}', shipping_data, timeout=timeout)
    
    @staticmethod
    def invalidate_product(product_id):
        """Invalider le cache d'un produit"""
        cache.delete(f'cj:product:{product_id}')
        logger.info(f"[Cache] Produit {product_id} invalidé")
    
    @staticmethod
    def invalidate_category(category_id):
        """Invalider le cache d'une catégorie"""
        cache.delete(f'cj:products:{category_id}')
        logger.info(f"[Cache] Catégorie {category_id} invalidée")
    
    @staticmethod
    def clear_all():
        """Vider tout le cache CJ"""
        cache.clear()
        logger.warning("[Cache] Tout le cache a été vidé")
