"""
Cache de fragments de templates pour MultiProShop
Permet de cacher des portions de templates pour éviter le re-rendering
"""
from flask import current_app
from functools import wraps
from extensions import cache
import hashlib

def cache_fragment(timeout=300, key_prefix='fragment'):
    """
    Décorateur pour cacher un fragment de template
    
    Usage dans un template:
    {% cache 300, 'sidebar_categories' %}
        ... contenu à cacher ...
    {% endcache %}
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Générer une clé unique basée sur les arguments
            cache_key = f"{key_prefix}_{hashlib.md5(str(args).encode() + str(kwargs).encode()).hexdigest()}"
            
            # Essayer de récupérer du cache
            result = cache.get(cache_key)
            
            if result is None:
                # Exécuter la fonction et mettre en cache
                result = f(*args, **kwargs)
                cache.set(cache_key, result, timeout=timeout)
            
            return result
        
        return decorated_function
    return decorator


def register_cache_extension(app):
    """Enregistrer l'extension de cache pour Jinja2"""
    
    from jinja2 import nodes
    from jinja2.ext import Extension
    
    class CacheExtension(Extension):
        """Extension Jinja2 pour le cache de fragments"""
        
        tags = {'cache'}
        
        def parse(self, parser):
            lineno = next(parser.stream).lineno
            
            # Parser les arguments: timeout et nom
            args = [parser.parse_expression()]
            
            if parser.stream.skip_if('comma'):
                args.append(parser.parse_expression())
            else:
                args.append(nodes.Const('default'))
            
            # Parser le corps du bloc
            body = parser.parse_statements(['name:endcache'], drop_needle=True)
            
            # Créer le nœud de cache
            return nodes.CallBlock(
                self.call_method('_cache_support', args),
                [], [], body
            ).set_lineno(lineno)
        
        def _cache_support(self, timeout, fragment_name, caller):
            """Méthode de support pour le cache"""
            from flask import request
            
            # Générer une clé unique
            key = f'fragment_{fragment_name}_{request.path}'
            
            # Essayer de récupérer du cache
            rv = cache.get(key)
            
            if rv is not None:
                return rv
            
            # Générer le contenu
            rv = caller()
            
            # Mettre en cache
            cache.set(key, rv, timeout=timeout)
            
            return rv
    
    # Ajouter l'extension à Jinja2
    app.jinja_env.add_extension(CacheExtension)
    
    print("[OK] Extension de cache de fragments enregistree")
    
    return app


def cache_template_fragment(fragment_name, timeout=300):
    """
    Helper pour cacher un fragment de template depuis Python
    
    Args:
        fragment_name: Nom unique du fragment
        timeout: Durée du cache en secondes
    
    Returns:
        Décorateur
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            key = f'template_fragment_{fragment_name}'
            
            result = cache.get(key)
            
            if result is None:
                result = f(*args, **kwargs)
                cache.set(key, result, timeout=timeout)
            
            return result
        
        return decorated_function
    return decorator
