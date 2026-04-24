"""
HTTP/2 Server Push pour MultiProShop
Envoie les ressources critiques avant que le navigateur ne les demande
"""
from flask import make_response

def add_server_push(response, resources):
    """
    Ajoute les headers Link pour HTTP/2 Server Push
    
    Args:
        response: Objet Response Flask
        resources: Liste de tuples (url, type) à pusher
                  Exemple: [('/static/css/styles.css', 'style'), ...]
    
    Returns:
        Response modifiée
    """
    if not resources:
        return response
    
    # Construire le header Link
    link_headers = []
    for url, resource_type in resources:
        link_headers.append(f'<{url}>; rel=preload; as={resource_type}')
    
    # Ajouter le header
    response.headers['Link'] = ', '.join(link_headers)
    
    return response


def push_critical_resources(f):
    """
    Décorateur pour pusher automatiquement les ressources critiques
    
    Usage:
    @app.route('/')
    @push_critical_resources
    def index():
        return render_template('index.html')
    """
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        response = make_response(f(*args, **kwargs))
        
        # Ressources critiques à pusher
        critical_resources = [
            ('/static/css/styles.css', 'style'),
            ('/static/css/layout_modern.css', 'style'),
            ('/static/js/cart.js', 'script'),
            ('https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css', 'style'),
            ('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css', 'style'),
        ]
        
        return add_server_push(response, critical_resources)
    
    return decorated_function


def init_http2_push(app):
    """Initialiser HTTP/2 Server Push sur les routes principales"""
    
    # Ajouter un after_request handler pour les pages principales
    @app.after_request
    def add_http2_push_headers(response):
        """Ajouter les headers de push sur les pages principales"""
        from flask import request
        
        # Pages principales qui bénéficient du push
        push_pages = ['/', '/products', '/products/']
        
        if request.path in push_pages and response.status_code == 200:
            critical_resources = [
                ('/static/css/styles.css', 'style'),
                ('/static/css/layout_modern.css', 'style'),
                ('/static/js/cart.js', 'script'),
            ]
            
            response = add_server_push(response, critical_resources)
        
        return response
    
    print("[OK] HTTP/2 Server Push configure")
    
    return app


def get_resource_hints():
    """
    Retourne les hints de ressources pour les templates
    
    Usage dans un template:
    {% for url, rel, type in get_resource_hints() %}
        <link rel="{{ rel }}" href="{{ url }}" as="{{ type }}">
    {% endfor %}
    """
    return [
        ('/static/css/styles.css', 'preload', 'style'),
        ('/static/css/layout_modern.css', 'preload', 'style'),
        ('/static/js/cart.js', 'preload', 'script'),
        ('https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css', 'preload', 'style'),
        ('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css', 'preload', 'style'),
    ]
