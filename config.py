"""
Configuration centralisée pour MultiProShop
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Charger les variables d'environnement AVANT la classe Config
load_dotenv()

# Chemin de base du projet
BASE_DIR = Path(__file__).parent.absolute()

class Config:
    """Configuration de base"""
    
    # Sécurité
    SECRET_KEY = os.getenv('SECRET_KEY', 'votre_clé_secrète_ici')
    
    # Base de données
    DB_PATH = BASE_DIR / 'instance' / 'multiproshop.db'
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{DB_PATH}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_POOL_RECYCLE = 280
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
    WTF_CSRF_ENABLED = False


# Configuration par défaut
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
