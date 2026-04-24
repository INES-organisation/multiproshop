"""
Monitoring de performance pour MultiProShop
Permet de détecter les requêtes lentes et d'optimiser en continu
"""
import time
from flask import g, request
import logging

logger = logging.getLogger(__name__)

def init_performance_monitoring(app):
    """Initialiser le monitoring de performance"""
    
    @app.before_request
    def before_request():
        """Démarrer le chronomètre avant chaque requête"""
        g.start_time = time.time()
        g.request_path = request.path
    
    @app.after_request
    def after_request(response):
        """Mesurer le temps de réponse après chaque requête"""
        if hasattr(g, 'start_time'):
            elapsed = time.time() - g.start_time
            
            # Log des requêtes lentes (> 1 seconde)
            if elapsed > 1.0:
                logger.warning(
                    f"⚠️  REQUÊTE LENTE: {g.request_path} - {elapsed:.2f}s - "
                    f"Méthode: {request.method} - Status: {response.status_code}"
                )
            
            # Log des requêtes très lentes (> 3 secondes)
            elif elapsed > 3.0:
                logger.error(
                    f"❌ REQUÊTE TRÈS LENTE: {g.request_path} - {elapsed:.2f}s - "
                    f"Méthode: {request.method} - Status: {response.status_code}"
                )
            
            # Ajouter le header de temps de réponse
            response.headers['X-Response-Time'] = f"{elapsed:.3f}s"
        
        return response
    
    @app.route('/api/performance/stats')
    def performance_stats():
        """Endpoint pour voir les statistiques de performance"""
        from flask import jsonify
        
        # Statistiques basiques (à améliorer avec une vraie DB de métriques)
        stats = {
            'status': 'ok',
            'monitoring': 'active',
            'cache_enabled': app.config.get('CACHE_TYPE') == 'RedisCache',
            'debug_mode': app.config.get('DEBUG', False),
            'scheduler_active': not app.config.get('DEBUG', True),
            'optimizations': {
                'context_processor_cache': True,
                'sidebar_optimized': True,
                'database_indexes': True,
                'lazy_loading_blueprints': True,
                'products_cache': True
            }
        }
        
        return jsonify(stats)
    
    logger.info("✅ Monitoring de performance activé")
