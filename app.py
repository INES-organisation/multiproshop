"""
Application Flask MultiProShop - Version Optimisée
"""
from flask import Flask, redirect, url_for
from extensions import db, login_manager, mail, cache
from flask_compress import Compress
from assets import init_assets
from config import config
import os
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()

# Initialiser la compression
compress = Compress()


def create_app(config_name='development'):
    """Factory pour créer l'application Flask"""
    app = Flask(__name__)
    
    # Charger la configuration
    app.config.from_object(config[config_name])
    if config_name == 'production' and app.config['SECRET_KEY'] == 'votre_clé_secrète_ici':
        raise RuntimeError("SECRET_KEY manquante : la définir dans l'environnement de production")
    if config_name == 'production':
        # Derrière ines-nginx : schéma https et IP client réels pour url_for(_external=True)
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
    
    # Afficher info DB au démarrage
    print(f"\n{'='*70}")
    print(f"MULTIPROSHOP - MODE: {config_name.upper()}")
    from sqlalchemy.engine import make_url
    print(f"Base de donnees: {make_url(app.config['SQLALCHEMY_DATABASE_URI']).render_as_string(hide_password=True)}")
    print(f"Cache: {app.config['CACHE_TYPE']}")
    print(f"{'='*70}\n")
    
    # Créer les dossiers nécessaires
    for folder in ['static/images', 'templates/auth', 'templates/products', 'templates/cart']:
        os.makedirs(os.path.join(app.root_path, folder), exist_ok=True)
    
    # Initialiser les extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    mail.init_app(app)
    cache.init_app(app)
    compress.init_app(app)
    init_assets(app)
    
    # Optimisations templates
    from utils.template_utils import register_template_filters
    register_template_filters(app)
    
    # Filtre d'optimisation d'images
    from utils.image_optimizer import register_image_filter
    register_image_filter(app)
    
    # Filtre de lazy loading automatique
    from utils.lazy_loading_helper import register_lazy_loading_filter
    register_lazy_loading_filter(app)
    
    # Cache de fragments de templates
    from utils.template_cache import register_cache_extension
    register_cache_extension(app)
    
    # HTTP/2 Server Push
    from utils.http2_push import init_http2_push
    init_http2_push(app)
    
    # Monitoring de performance
    from utils.performance_monitor import init_performance_monitoring
    init_performance_monitoring(app)
    
    # Importer les modèles
    from models import Role, User, Category, Product, Order, OrderItem
    from models.product_variant import ProductVariant
    from models.cart_reminder import CartReminder
    from models.review_request import ReviewRequest
    
    # Créer les tables
    with app.app_context():
        db.create_all()
        # gunicorn --preload : ne pas partager les connexions du processus maître avec les workers
        db.engine.dispose()
    
    # Context processor - recharge les catégories à chaque requête pour éviter les instances détachées
    @app.context_processor
    def inject_global_vars():
        from utils.datetime_utils import now_naive
        
        # Récupérer les catégories principales (pas de cache pour éviter DetachedInstanceError)
        # Exclure les catégories CJ (visible=False)
        from services.product_service import ProductService
        menu_ids = ProductService.menu_category_ids()
        main_categories = [c for c in Category.query.filter_by(
            level=1, is_active=True, visible=True
        ).order_by(Category.order, Category.name).all() if c.id in menu_ids]
        
        return {
            'now': now_naive(),
            'main_categories': main_categories,
            'menu_ids': menu_ids,
            'site_url': app.config['SITE_URL'],
            'seller': app.config['SELLER'],
            'free_shipping_threshold': app.config['FREE_SHIPPING_THRESHOLD'],
            'return_days': app.config['RETURN_DAYS'],
            'delivery_days': app.config['DELIVERY_DAYS'],
            'delivery_window': delivery_window,
            'analytics': {k: v for k, v in app.config['ANALYTICS'].items() if v},
        }

    def delivery_window():
        """Dates de livraison estimées (jours ouvrés, à partir d'aujourd'hui), ex. « 6 nov. et 18 nov. »"""
        from datetime import date, timedelta
        months = ('janv.', 'févr.', 'mars', 'avr.', 'mai', 'juin', 'juil.', 'août', 'sept.', 'oct.', 'nov.', 'déc.')
        def add_business_days(day, n):
            while n:
                day += timedelta(days=1)
                n -= day.weekday() < 5
            return day
        return tuple(f'{d.day} {months[d.month - 1]}' for d in
                     (add_business_days(date.today(), n) for n in app.config['DELIVERY_BUSINESS_DAYS']))
    
    # Enregistrer les blueprints
    register_blueprints(app)
    
    # Initialiser le scheduler
    init_scheduler(app)
    
    return app


def register_blueprints(app):
    """Enregistrer tous les blueprints - Optimisé avec lazy loading"""
    
    # === BLUEPRINTS ESSENTIELS (toujours chargés) ===
    from routes.main import main as main_blueprint
    from routes.auth import auth as auth_blueprint
    from routes.products import products as products_blueprint
    from routes.cart import cart_bp as cart_blueprint
    from routes.errors import errors_bp
    from routes.search import search_bp
    
    app.register_blueprint(main_blueprint)
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    app.register_blueprint(errors_bp)
    app.register_blueprint(products_blueprint, url_prefix='/products')
    app.register_blueprint(cart_blueprint, url_prefix='/cart')
    app.register_blueprint(search_bp)
    
    # === BLUEPRINTS UTILISATEUR (chargés si activés) ===
    if app.config.get('ENABLE_USER_FEATURES', True):
        from routes.user import user_bp as user_blueprint
        app.register_blueprint(user_blueprint, url_prefix='/user')
    
    # === BLUEPRINTS ADMIN (chargés seulement si nécessaire) ===
    if app.config.get('ENABLE_ADMIN', True):
        from routes.admin import admin_bp
        from routes.admin_cj_sync import bp as admin_cj_sync_bp
        from routes.admin_cj_pages import bp as admin_cj_pages_bp
        from routes.admin_cj_api import bp as admin_cj_api_bp
        from routes.admin_cj_orders import admin_cj_orders
        from routes.admin_cj_dashboard import admin_cj_dashboard
        from routes.admin_pricing import admin_pricing_bp
        from routes.admin_celery_dashboard import bp as admin_celery_bp
        
        app.register_blueprint(admin_bp, url_prefix='/admin')
        app.register_blueprint(admin_cj_sync_bp)
        app.register_blueprint(admin_cj_pages_bp)
        app.register_blueprint(admin_cj_api_bp)
        app.register_blueprint(admin_cj_orders)
        app.register_blueprint(admin_cj_dashboard)
        app.register_blueprint(admin_pricing_bp)
        app.register_blueprint(admin_celery_bp)
    
    # === BLUEPRINTS API (chargés si activés) ===
    if app.config.get('ENABLE_API', True):
        from routes.api import api_blueprint
        from routes.api_management import api_mgmt_bp
        from routes.api_products import bp as api_products_bp
        from routes.api_shipping import bp as api_shipping_bp
        from routes.api_reviews import bp as api_reviews_bp
        from routes.shipping_api import bp as shipping_api_bp
        
        app.register_blueprint(api_blueprint, url_prefix='/api')
        app.register_blueprint(api_mgmt_bp)
        app.register_blueprint(api_products_bp)
        app.register_blueprint(api_shipping_bp)
        app.register_blueprint(api_reviews_bp)
        app.register_blueprint(shipping_api_bp)
    
    # === BLUEPRINTS WEBHOOKS (chargés si activés) ===
    if app.config.get('ENABLE_WEBHOOKS', True):
        from routes.webhooks import webhooks_bp
        from routes.webhooks_cj import webhooks_cj
        
        app.register_blueprint(webhooks_bp)
        app.register_blueprint(webhooks_cj)
    
    # === BLUEPRINTS FONCTIONNALITÉS AVANCÉES (optionnels) ===
    if app.config.get('ENABLE_ADVANCED_FEATURES', False):
        from routes.supplier import supplier_blueprint
        from routes.marketplace import marketplace_blueprint
        from routes.video import video_blueprint
        from routes.ai import ai_blueprint
        
        app.register_blueprint(supplier_blueprint, url_prefix='/suppliers')
        app.register_blueprint(marketplace_blueprint, url_prefix='/marketplaces')
        app.register_blueprint(video_blueprint, url_prefix='/videos')
        app.register_blueprint(ai_blueprint, url_prefix='/ai')
    
    # === BLUEPRINTS UTILITAIRES (toujours chargés) ===
    from routes.shipping import bp as shipping_bp
    from routes.product_variants import bp as product_variants_bp
    from routes.sitemap import sitemap_bp
    from routes.health import health_bp
    from routes.api_docs import api_docs_bp
    from routes.faq import faq_bp
    
    app.register_blueprint(shipping_bp)
    app.register_blueprint(product_variants_bp)
    app.register_blueprint(sitemap_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(api_docs_bp)
    app.register_blueprint(faq_bp)
    
    # === BLUEPRINTS DE TEST (seulement en dev) ===
    if app.config.get('DEBUG', False):
        from routes.test_categories import test_bp
        app.register_blueprint(test_bp)
    
    # Route de redirection
    @app.route('/multiproshop/')
    def multiproshop_root():
        return redirect(url_for('main.index'))


def init_scheduler(app):
    """Initialiser le scheduler de synchronisation"""
    # Ne démarrer le scheduler qu'en production pour économiser des ressources
    if not app.config.get('DEBUG', True):
        from services.sync_scheduler import get_scheduler
        scheduler = get_scheduler(app)
        
        # Enregistrer le shutdown
        import atexit
        atexit.register(lambda: scheduler.shutdown())
        print("✅ Scheduler de synchronisation activé (mode production)")
    else:
        print("[INFO] Scheduler desactive en mode developpement (optimisation performance)")


# Créer l'application
app = create_app(os.getenv('FLASK_ENV', 'development'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
