"""
Utilitaire pour optimiser les images avec lazy loading
Ajoute automatiquement les attributs loading="lazy" et decoding="async"
"""

def optimize_image_tag(url, alt="", css_class="", width=None, height=None):
    """
    Génère un tag img optimisé avec lazy loading
    
    Args:
        url: URL de l'image
        alt: Texte alternatif
        css_class: Classes CSS
        width: Largeur (optionnel)
        height: Hauteur (optionnel)
    
    Returns:
        str: Tag HTML optimisé
    """
    attrs = [
        f'src="{url}"',
        f'alt="{alt}"',
        'loading="lazy"',
        'decoding="async"'
    ]
    
    if css_class:
        attrs.append(f'class="{css_class}"')
    
    if width:
        attrs.append(f'width="{width}"')
    
    if height:
        attrs.append(f'height="{height}"')
    
    return f'<img {" ".join(attrs)}>'


def register_image_filter(app):
    """Enregistrer le filtre Jinja2 pour les images optimisées"""
    
    @app.template_filter('lazy_img')
    def lazy_img_filter(url, alt="", css_class=""):
        """
        Filtre Jinja2 pour générer des images avec lazy loading
        
        Usage dans les templates:
        {{ product.image_url | lazy_img(product.name, 'product-img') }}
        """
        return optimize_image_tag(url, alt, css_class)
    
    return app
