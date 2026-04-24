"""
Utilitaires pour optimiser les templates Jinja2
"""
from jinja2 import nodes
from jinja2.ext import Extension
from extensions import cache


class FragmentCacheExtension(Extension):
    """
    Extension Jinja2 pour cacher des fragments de templates
    
    Usage dans les templates:
        {% cache 'key', 300 %}
            <div>Contenu à cacher</div>
        {% endcache %}
    """
    
    tags = {'cache'}
    
    def __init__(self, environment):
        super().__init__(environment)
        environment.globals['cache_get'] = cache.get
        environment.globals['cache_set'] = cache.set
    
    def parse(self, parser):
        lineno = next(parser.stream).lineno
        
        # Parse les arguments
        args = [parser.parse_expression()]
        
        # Parse le timeout si fourni
        if parser.stream.skip_if('comma'):
            args.append(parser.parse_expression())
        else:
            args.append(nodes.Const(300))
        
        # Parse le corps du bloc
        body = parser.parse_statements(['name:endcache'], drop_needle=True)
        
        return nodes.CallBlock(
            self.call_method('_cache_support', args),
            [], [], body
        ).set_lineno(lineno)
    
    def _cache_support(self, key, timeout, caller):
        """Méthode appelée pour gérer le cache"""
        # Vérifier le cache
        rv = cache.get(key)
        if rv is not None:
            return rv
        
        # Générer le contenu
        rv = caller()
        
        # Mettre en cache
        cache.set(key, rv, timeout=timeout)
        return rv


def format_price(value):
    """Formater un prix en euros"""
    if value is None:
        return "0,00 €"
    return f"{value:,.2f} €".replace(',', ' ').replace('.', ',')


def format_number(value):
    """Formater un nombre avec séparateurs"""
    if value is None:
        return "0"
    return f"{value:,}".replace(',', ' ')


def truncate_smart(text, length=100, suffix='...'):
    """
    Tronquer un texte intelligemment (coupe au mot)
    """
    if not text or len(text) <= length:
        return text
    
    # Trouver le dernier espace avant la limite
    truncated = text[:length].rsplit(' ', 1)[0]
    return truncated + suffix


def pluralize(count, singular, plural=None):
    """
    Pluraliser un mot selon le nombre
    
    Usage:
        {{ count|pluralize('produit', 'produits') }}
    """
    if plural is None:
        plural = singular + 's'
    return singular if count == 1 else plural


def register_template_filters(app):
    """Enregistrer tous les filtres personnalisés"""
    app.jinja_env.filters['format_price'] = format_price
    app.jinja_env.filters['format_number'] = format_number
    app.jinja_env.filters['truncate_smart'] = truncate_smart
    app.jinja_env.filters['pluralize'] = pluralize
    
    # Ajouter l'extension de cache
    app.jinja_env.add_extension(FragmentCacheExtension)
    
    # Optimisations Jinja2
    app.jinja_env.auto_reload = False  # Désactiver auto-reload en prod
    app.jinja_env.cache_size = 400  # Augmenter le cache de templates
