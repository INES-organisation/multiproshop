# Ce fichier permet de charger tous les modèles dans le bon ordre
# pour éviter les problèmes de dépendances circulaires

from extensions import db

# Import des modèles dans l'ordre des dépendances
from .role import Role
from .user import User
from .category import Category
from .marketplace import Marketplace
from .product import Product
from .order import Order, OrderItem
from .supplier import Supplier
from .video import Video
from .ai_recommendation import AIRecommendation
from .api_integration import ApiIntegration
from .api_provider import ApiProvider, CategoryMapping, ProductSource, ApiSyncLog
from .shipping_rate import ShippingRate

# Cette liste est utilisée pour faciliter l'importation des modèles ailleurs dans l'application
__all__ = [
    'Role',
    'User',
    'Category',
    'Marketplace',
    'Product',
    'Order',
    'OrderItem',
    'Supplier',
    'Video',
    'AIRecommendation',
    'ApiIntegration',
    'ApiProvider',
    'CategoryMapping',
    'ProductSource',
    'ApiSyncLog',
    'ShippingRate'
]
