"""
Configuration centralisée pour MultiProShop
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Charger les variables d'environnement AVANT la classe Config
load_dotenv()


def load_ines_site_config():
    """Clés de la boutique gérées dans INES (/admin/integrations, préfixe MULTIPROSHOP_, ex.
    MULTIPROSHOP_CJ_DEV_KEY) : lues au démarrage et prioritaires sur l'environnement. Une clé
    modifiée dans INES est prise en compte au redémarrage des conteneurs. INES injoignable :
    on garde l'environnement (deploy/.env) et on le signale."""
    if not os.getenv('INES_API_KEY'):
        return
    import logging
    import requests
    url = os.getenv('INES_API_URL', 'http://ines-backend:8000').rstrip('/') + '/api/v1/external/site-config/multiproshop'
    try:
        r = requests.get(url, headers={'Authorization': 'Bearer ' + os.environ['INES_API_KEY']}, timeout=5)
        r.raise_for_status()
        os.environ.update({k: str(v) for k, v in r.json().items()})
    except Exception as e:  # noqa: BLE001 — le site doit démarrer même si INES est en panne
        logging.getLogger(__name__).error("Configuration INES non chargée (%s) : clés de deploy/.env utilisées", e)


load_ines_site_config()

# Chemin de base du projet
BASE_DIR = Path(__file__).parent.absolute()

class Config:
    """Configuration de base"""
    
    # Sécurité
    SECRET_KEY = os.getenv('SECRET_KEY', 'votre_clé_secrète_ici')

    # Boutique : une seule source pour ce qui est promis au client (bandeau, fiche, panier,
    # paiement, CGV) et pour l'identité du vendeur (mentions légales, CGV, pied de page)
    SITE_URL = os.getenv('SITE_URL', 'https://multiproshop.com').rstrip('/')
    FREE_SHIPPING_THRESHOLD = float(os.getenv('FREE_SHIPPING_THRESHOLD', '50'))
    FREE_SHIPPING_COUNTRIES = ('FR',)  # France métropolitaine
    RETURN_DAYS = 14
    DELIVERY_DAYS = '7 à 15 jours ouvrés'
    DELIVERY_BUSINESS_DAYS = (7, 15)  # même fourchette, pour la date de livraison estimée
    # Mesure d'audience et publicité : rien n'est chargé sans identifiant ni sans accord du visiteur
    ANALYTICS = {
        'ga4': os.getenv('GA4_MEASUREMENT_ID', ''),
        'meta': os.getenv('META_PIXEL_ID', ''),
        'tiktok': os.getenv('TIKTOK_PIXEL_ID', ''),
    }
    SELLER = {
        'company': 'TONY ALPHA 8.0',
        'trade_name': 'MultiProShop',
        'owner': 'Anthony Michel Legros',
        'publisher': 'Anthony Legros',
        'legal_form': 'Entrepreneur individuel (EI)',
        'siren': '844 384 198',
        'address': '8 bis impasse des Jonquilles',
        'postal_code': '97430',
        'city': 'Le Tampon',
        'region': 'La Réunion, France',
        'phone': '06 93 48 78 17',
        'phone_link': '+262693487817',
        'email': os.getenv('CONTACT_EMAIL', 'contact@multiproshop.com'),
        'vat': 'TVA non applicable, article 293 B du CGI',
        'hours': 'du lundi au vendredi, 9h-18h (heure de La Réunion)',
    }

    # Base de données : DATABASE_URL (PostgreSQL en production), SQLite local par défaut
    DB_PATH = BASE_DIR / 'instance' / 'multiproshop.db'
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL') or f'sqlite:///{DB_PATH}'
    if SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_POOL_RECYCLE = 280
    if SQLALCHEMY_DATABASE_URI.startswith('sqlite'):
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_size': 10,              # Nombre de connexions dans le pool
            'max_overflow': 20,            # Connexions supplémentaires autorisées
            'pool_timeout': 30,            # Timeout pour obtenir une connexion (secondes)
            'pool_pre_ping': True,         # Vérifier la connexion avant utilisation
            'connect_args': {
                'check_same_thread': False,  # Nécessaire pour SQLite multi-thread
                'timeout': 30                # Timeout pour les opérations DB
            }
        }
    else:
        # PostgreSQL partagé avec INES : peu de connexions par processus
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_size': 5,
            'max_overflow': 5,
            'pool_timeout': 30,
            'pool_pre_ping': True,
        }
    
    # Cache Redis (activé pour performance maximale)
    CACHE_TYPE = 'RedisCache'
    CACHE_REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes
    CACHE_OPTIONS = {
        'socket_connect_timeout': 5,
        'socket_timeout': 5,
        'socket_keepalive': True,
        'health_check_interval': 30,
    }
    
    # Compression
    COMPRESS_MIMETYPES = [
        'text/html',
        'text/css',
        'text/xml',
        'application/json',
        'application/javascript',
    ]
    COMPRESS_LEVEL = 6
    COMPRESS_MIN_SIZE = 500
    
    # Session
    SESSION_COOKIE_SECURE = False  # True en production avec HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_PATH = '/'
    SESSION_COOKIE_DOMAIN = None
    PERMANENT_SESSION_LIFETIME = 86400  # 24 heures
    SESSION_PERMANENT = False
    REMEMBER_COOKIE_DURATION = 86400
    
    # Stripe
    STRIPE_PUBLIC_KEY = os.getenv('STRIPE_PUBLIC_KEY', '')
    STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY', '')
    STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET', '')
    
    # Email
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True') == 'True'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@multiproshop.com')
    
    # CJ Dropshipping API
    CJ_EMAIL = os.getenv('CJ_EMAIL', '')
    CJ_PASSWORD = os.getenv('CJ_PASSWORD', '')
    CJ_DEV_KEY = os.getenv('CJ_DEV_KEY', '')
    CJ_BASE_URL = os.getenv('CJ_BASE_URL', 'https://developers.cjdropshipping.com/api2.0/v1/')
    CJ_TIMEOUT = int(os.getenv('CJ_TIMEOUT', 30))
    CJ_VERIFY_SSL = os.getenv('CJ_VERIFY_SSL', 'False') == 'True'
    CJ_CACHE_ENABLED = os.getenv('CJ_CACHE_ENABLED', 'True') == 'True'
    CJ_CACHE_DURATION = int(os.getenv('CJ_CACHE_DURATION', 3600))
    CJ_RATE_LIMIT_DELAY = int(os.getenv('CJ_RATE_LIMIT_DELAY', 1))
    CJ_DEFAULT_PAGE_SIZE = int(os.getenv('CJ_DEFAULT_PAGE_SIZE', 100))
    CJ_MAX_PAGES = int(os.getenv('CJ_MAX_PAGES', 500))
    CJ_DEBUG_ENABLED = os.getenv('CJ_DEBUG_ENABLED', 'True') == 'True'
    CJ_LOG_REQUESTS = os.getenv('CJ_LOG_REQUESTS', 'True') == 'True'


class DevelopmentConfig(Config):
    """Configuration développement"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Configuration production"""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    # En production, utiliser Redis
    CACHE_TYPE = 'RedisCache'
    CACHE_REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')


class TestingConfig(Config):
    """Configuration tests"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_ENGINE_OPTIONS = {}
    CACHE_TYPE = 'SimpleCache'
    CACHE_OPTIONS = {}
    WTF_CSRF_ENABLED = False


# Configuration par défaut
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
