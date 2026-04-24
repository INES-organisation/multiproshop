"""
Configuration Flask-Assets pour minification CSS/JS
"""
from flask_assets import Environment, Bundle

def init_assets(app):
    """Initialiser Flask-Assets avec bundles CSS et JS"""
    assets = Environment(app)
    
    # Configuration
    assets.url = app.static_url_path
    assets.directory = app.static_folder
    assets.debug = False  # Activer minification
    assets.auto_build = True
    
    # Bundle CSS - Styles principaux
    css_main = Bundle(
        'css/styles.css',
        'css/layout_modern.css',
        'css/home_modern.css',
        filters='cssmin',
        output='gen/main.min.css'
    )
    
    # Bundle CSS - Admin
    css_admin = Bundle(
        'css/admin_modern.css',
        filters='cssmin',
        output='gen/admin.min.css'
    )
    
    # Bundle JS - Scripts principaux
    js_main = Bundle(
        'js/main.js',
        'js/cart.js',
        filters='jsmin',
        output='gen/main.min.js'
    )
    
    # Bundle JS - Premium header
    js_premium = Bundle(
        'js/premium_header.js',
        filters='jsmin',
        output='gen/premium.min.js'
    )
    
    # Enregistrer les bundles
    assets.register('css_main', css_main)
    assets.register('css_admin', css_admin)
    assets.register('js_main', js_main)
    assets.register('js_premium', js_premium)
    
    return assets
