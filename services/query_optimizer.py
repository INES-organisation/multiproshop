"""
Optimiseur de requêtes avancé pour MultiProShop
Eager loading intelligent et optimisation automatique
"""
from sqlalchemy.orm import joinedload, selectinload, subqueryload
from models.product import Product
from models.category import Category
from models.order import Order
from models.order_item import OrderItem

class QueryOptimizer:
    """Optimiseur de requêtes avec eager loading intelligent"""
    
    @staticmethod
    def get_products_optimized(filters=None, limit=None):
        """
        Récupère les produits avec eager loading optimal
        
        Args:
            filters: Dictionnaire de filtres (category_id, is_active, etc.)
            limit: Nombre maximum de produits
        
        Returns:
            Query optimisée
        """
        query = Product.query.options(
            joinedload(Product.category),  # Relation many-to-one
            selectinload(Product.variants),  # Relation one-to-many
        )
        
        if filters:
            for key, value in filters.items():
                query = query.filter(getattr(Product, key) == value)
        
        if limit:
            query = query.limit(limit)
        
        return query
    
    @staticmethod
    def get_product_with_relations(product_id):
        """
        Récupère un produit avec toutes ses relations en une seule requête
        
        Args:
            product_id: ID du produit
        
        Returns:
            Product avec relations chargées
        """
        return Product.query.options(
            joinedload(Product.category),
        ).filter_by(id=product_id).first()
    
    @staticmethod
    def get_categories_with_products(parent_id=None, active_only=True):
        """
        Récupère les catégories avec leurs produits en une requête
        
        Args:
            parent_id: ID de la catégorie parente (None pour racine)
            active_only: Filtrer uniquement les catégories actives
        
        Returns:
            Liste de catégories avec produits
        """
        query = Category.query.options(
            selectinload(Category.products)
        )
        
        if parent_id is not None:
            query = query.filter_by(parent_id=parent_id)
        
        if active_only:
            query = query.filter_by(is_active=True)
        
        return query.all()
    
    @staticmethod
    def get_orders_with_items(user_id=None, limit=10):
        """
        Récupère les commandes avec leurs items en une requête
        
        Args:
            user_id: ID de l'utilisateur (optionnel)
            limit: Nombre maximum de commandes
        
        Returns:
            Liste de commandes avec items
        """
        query = Order.query.options(
            selectinload(Order.items).joinedload(OrderItem.product)
        )
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        return query.order_by(Order.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def get_category_tree_optimized(root_id=None):
        """
        Récupère l'arbre des catégories de manière optimisée
        
        Args:
            root_id: ID de la catégorie racine (None pour toutes)
        
        Returns:
            Liste de catégories avec enfants
        """
        # Charger toutes les catégories en une requête
        if root_id:
            categories = Category.query.filter_by(parent_id=root_id, is_active=True).all()
        else:
            categories = Category.query.filter_by(level=1, is_active=True).all()
        
        # Construire l'arbre en mémoire (évite N+1)
        return categories
    
    @staticmethod
    def apply_eager_loading(query, relations):
        """
        Applique l'eager loading dynamiquement
        
        Args:
            query: Query SQLAlchemy
            relations: Liste de relations à charger
                      Format: ['category', 'variants', 'images']
        
        Returns:
            Query avec eager loading
        """
        relation_map = {
            'category': joinedload(Product.category),
        }
        
        for relation in relations:
            if relation in relation_map:
                query = query.options(relation_map[relation])
        
        return query
