"""
Helper pour ajouter automatiquement le lazy loading sur les images dans les templates
"""

def add_lazy_loading_to_images(html_content):
    """
    Ajoute loading="lazy" et decoding="async" aux balises img
    
    Args:
        html_content: Contenu HTML
    
    Returns:
        str: HTML avec lazy loading ajouté
    """
    import re
    
    # Pattern pour trouver les balises img sans loading="lazy"
    pattern = r'<img\s+([^>]*?)(?<!loading=")(?<!loading=\')>'
    
    def add_attributes(match):
        attrs = match.group(1).strip()
        
        # Vérifier si loading ou decoding sont déjà présents
        has_loading = 'loading=' in attrs
        has_decoding = 'decoding=' in attrs
        
        # Ajouter les attributs manquants
        if not has_loading:
            attrs += ' loading="lazy"'
        if not has_decoding:
            attrs += ' decoding="async"'
        
        return f'<img {attrs}>'
    
    return re.sub(pattern, add_attributes, html_content)


def register_lazy_loading_filter(app):
    """Enregistrer le filtre Jinja2 pour le lazy loading automatique"""
    
    @app.template_filter('lazy_html')
    def lazy_html_filter(html):
        """
        Filtre Jinja2 pour ajouter lazy loading aux images dans du HTML
        
        Usage:
        {{ content | lazy_html | safe }}
        """
        return add_lazy_loading_to_images(html)
    
    return app
