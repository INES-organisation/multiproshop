"""
Service de gestion des produits
"""
from models.product import Product
from models.category import Category
from sqlalchemy import or_
from sqlalchemy.orm import joinedload


class ProductService:
    """Service pour gérer les opérations sur les produits"""
    
    @staticmethod
    def _get_category_ids_recursive(category_id):
        """
        Récupère l'ID de la catégorie + tous les IDs de ses sous-catégories (récursif).
        Permet d'afficher les produits de toute une branche de la hiérarchie.
        """
        ids = [category_id]
        children = Category.query.filter_by(parent_id=category_id, is_active=True).all()
        for child in children:
            ids.extend(ProductService._get_category_ids_recursive(child.id))
        return ids
    
    @staticmethod
    def get_products_paginated(page=1, per_page=12, sort_by='name', category_id=None):
        """
        Récupère les produits avec pagination et eager loading optimisé
        
        Args:
            page: Numéro de page
            per_page: Nombre de produits par page
            sort_by: Critère de tri ('name', 'price_asc', 'price_desc')
            category_id: ID de catégorie pour filtrer (optionnel)
            
        Returns:
            Pagination: Objet de pagination Flask-SQLAlchemy
        """
        # Eager loading optimisé : joinedload pour many-to-one
        query = Product.query.options(
            joinedload(Product.category)
        )
        
        # Filtrer par catégorie si spécifié (inclut les sous-catégories)
        if category_id:
            all_ids = ProductService._get_category_ids_recursive(category_id)
            query = query.filter(Product.category_id.in_(all_ids))
        
        # Appliquer le tri
        if sort_by == 'price_asc':
            query = query.order_by(Product.price.asc())
        elif sort_by == 'price_desc':
            query = query.order_by(Product.price.desc())
        else:
            query = query.order_by(Product.name.asc())
        
        return query.paginate(page=page, per_page=per_page)
    
    @staticmethod
    def search_products(search_query):
        """
        Recherche des produits par nom ou description
        
        Args:
            search_query: Terme de recherche
            
        Returns:
            list: Liste de produits correspondants
        """
        if not search_query:
            return []
        
        search_pattern = f"%{search_query}%"
        return Product.query.options(joinedload(Product.category)).filter(
            or_(
                Product.name.ilike(search_pattern),
                Product.description.ilike(search_pattern)
            )
        ).all()
    
    @staticmethod
    def get_product_by_id(product_id):
        """
        Récupère un produit par son ID
        
        Args:
            product_id: ID du produit
            
        Returns:
            Product or None: Le produit ou None si introuvable
        """
        return Product.query.options(
            joinedload(Product.category),
            joinedload(Product.sources)
        ).get(product_id)
    
    @staticmethod
    def get_related_products(product, limit=4):
        """
        Récupère les produits liés (même catégorie)
        
        Args:
            product: Produit de référence
            limit: Nombre maximum de produits à retourner
            
        Returns:
            list: Liste de produits liés
        """
        return Product.query.options(joinedload(Product.category)).filter_by(
            category_id=product.category_id
        ).filter(
            Product.id != product.id
        ).limit(limit).all()
    
    @staticmethod
    def get_products_by_category(category_id, page=1, per_page=12):
        """
        Récupère les produits d'une catégorie avec pagination
        
        Args:
            category_id: ID de la catégorie
            page: Numéro de page (défaut: 1)
            per_page: Produits par page (défaut: 12)
            
        Returns:
            Pagination: Objet de pagination Flask-SQLAlchemy
        """
        # Inclure les produits des sous-catégories
        all_ids = ProductService._get_category_ids_recursive(category_id)
        query = Product.query.options(joinedload(Product.category)).filter(
            Product.category_id.in_(all_ids)
        )
        
        # Si page=None, retourner tous les produits (compatibilité)
        if page is None:
            return query.all()
        
        return query.paginate(page=page, per_page=per_page, error_out=False)
    
    @staticmethod
    def check_stock_availability(product_id, quantity):
        """
        Vérifie la disponibilité du stock
        
        Args:
            product_id: ID du produit
            quantity: Quantité demandée
            
        Returns:
            tuple: (available: bool, product: Product or None)
        """
        product = Product.query.get(product_id)
        
        if not product:
            return False, None
        
        return product.stock >= quantity, product
    
    @staticmethod
    def update_stock(product_id, quantity_change):
        """
        Met à jour le stock d'un produit
        
        Args:
            product_id: ID du produit
            quantity_change: Changement de quantité (positif ou négatif)
            
        Returns:
            tuple: (success: bool, product: Product or None)
        """
        product = Product.query.get(product_id)
        
        if not product:
            return False, None
        
        new_stock = product.stock + quantity_change
        
        if new_stock < 0:
            return False, product
        
        product.stock = new_stock
        return True, product
    
    @staticmethod
    def get_featured_products(limit=8):
        """
        Récupère les produits en vedette pour la page d'accueil
        
        Args:
            limit: Nombre de produits à retourner
            
        Returns:
            list: Liste de produits en vedette
        """
        return Product.query.options(joinedload(Product.category)).limit(limit).all()
    
    @staticmethod
    def get_deals_of_the_day(limit=8):
        """
        Récupère les offres du jour (produits récents)
        
        Args:
            limit: Nombre de produits à retourner
            
        Returns:
            list: Liste de produits en promotion
        """
        return Product.query.options(joinedload(Product.category)).order_by(Product.id.desc()).limit(limit).all()
    
    @staticmethod
    def get_suggestions(limit=8):
        """
        Récupère des suggestions de produits
        
        Args:
            limit: Nombre de produits à retourner
            
        Returns:
            list: Liste de produits suggérés
        """
        return Product.query.options(joinedload(Product.category)).order_by(Product.id.asc()).limit(limit).all()
    
    @staticmethod
    def get_new_arrivals(limit=4):
        """
        Récupère les nouveautés (derniers produits ajoutés)
        
        Args:
            limit: Nombre de produits à retourner
            
        Returns:
            list: Liste des nouveaux produits
        """
        return Product.query.options(joinedload(Product.category)).order_by(Product.created_at.desc()).limit(limit).all()
