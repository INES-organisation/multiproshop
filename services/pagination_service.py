"""
Service de pagination optimisée avec cursors
Plus rapide que OFFSET/LIMIT sur les grandes tables
"""
from models.product import Product
from sqlalchemy.orm import joinedload

class PaginationService:
    """Service de pagination optimisée"""
    
    @staticmethod
    def get_products_cursor(cursor=None, limit=20, category_id=None, sort_by='id'):
        """
        Pagination avec cursors (plus rapide que OFFSET/LIMIT)
        
        Args:
            cursor: ID du dernier produit de la page précédente
            limit: Nombre de produits par page
            category_id: Filtrer par catégorie (optionnel)
            sort_by: Champ de tri ('id', 'price', 'name')
        
        Returns:
            tuple: (produits, next_cursor, has_next)
        """
        query = Product.query.filter_by(is_active=True)
        
        # Filtrer par catégorie si spécifié
        if category_id:
            query = query.filter_by(category_id=category_id)
        
        # Appliquer le cursor
        if cursor:
            if sort_by == 'price':
                query = query.filter(Product.price > cursor)
            elif sort_by == 'name':
                query = query.filter(Product.name > cursor)
            else:  # 'id' par défaut
                query = query.filter(Product.id > cursor)
        
        # Eager loading pour éviter N+1
        query = query.options(joinedload(Product.category))
        
        # Trier et limiter
        if sort_by == 'price':
            query = query.order_by(Product.price)
        elif sort_by == 'name':
            query = query.order_by(Product.name)
        else:
            query = query.order_by(Product.id)
        
        # Récupérer limit + 1 pour savoir s'il y a une page suivante
        products = query.limit(limit + 1).all()
        
        # Vérifier s'il y a une page suivante
        has_next = len(products) > limit
        if has_next:
            products = products[:limit]
        
        # Calculer le next_cursor
        if products and has_next:
            last_product = products[-1]
            if sort_by == 'price':
                next_cursor = last_product.price
            elif sort_by == 'name':
                next_cursor = last_product.name
            else:
                next_cursor = last_product.id
        else:
            next_cursor = None
        
        return products, next_cursor, has_next
    
    @staticmethod
    def get_products_offset(page=1, per_page=20, category_id=None, sort_by='id'):
        """
        Pagination classique avec OFFSET/LIMIT (pour compatibilité)
        
        Args:
            page: Numéro de page
            per_page: Produits par page
            category_id: Filtrer par catégorie
            sort_by: Champ de tri
        
        Returns:
            Pagination object
        """
        query = Product.query.filter_by(is_active=True)
        
        if category_id:
            query = query.filter_by(category_id=category_id)
        
        query = query.options(joinedload(Product.category))
        
        if sort_by == 'price':
            query = query.order_by(Product.price)
        elif sort_by == 'name':
            query = query.order_by(Product.name)
        else:
            query = query.order_by(Product.id.desc())
        
        return query.paginate(page=page, per_page=per_page, error_out=False)
