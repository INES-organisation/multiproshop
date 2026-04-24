"""
Service de recherche avancée pour les produits
Phase 3.2 - Recherche full-text avec scoring
"""
from typing import Dict, List, Optional
from sqlalchemy import or_, and_, func
from models.product import Product
from models.category import Category
from extensions import db, cache
import logging

logger = logging.getLogger(__name__)


class SearchService:
    """Service de recherche de produits"""
    
    def __init__(self):
        """Initialiser le service de recherche"""
        pass
    
    def search_products(
        self,
        query: str,
        category_id: Optional[int] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        in_stock_only: bool = False,
        sort_by: str = 'relevance',
        page: int = 1,
        per_page: int = 20
    ) -> Dict:
        """
        Rechercher des produits avec filtres
        
        Args:
            query: Terme de recherche
            category_id: Filtrer par catégorie
            min_price: Prix minimum
            max_price: Prix maximum
            in_stock_only: Uniquement produits en stock
            sort_by: Tri (relevance, price_asc, price_desc, name, newest)
            page: Numéro de page
            per_page: Résultats par page
            
        Returns:
            dict: Résultats avec pagination
        """
        try:
            # Base query
            base_query = Product.query.filter(Product.is_active == True)
            
            # Recherche full-text
            if query and query.strip():
                search_term = f"%{query.strip()}%"
                base_query = base_query.filter(
                    or_(
                        Product.name.ilike(search_term),
                        Product.description.ilike(search_term),
                        Product.sku.ilike(search_term)
                    )
                )
            
            # Filtre catégorie
            if category_id:
                base_query = base_query.filter(Product.category_id == category_id)
            
            # Filtre prix
            if min_price is not None:
                base_query = base_query.filter(Product.price >= min_price)
            if max_price is not None:
                base_query = base_query.filter(Product.price <= max_price)
            
            # Filtre stock
            if in_stock_only:
                base_query = base_query.filter(Product.stock > 0)
            
            # Tri
            if sort_by == 'price_asc':
                base_query = base_query.order_by(Product.price.asc())
            elif sort_by == 'price_desc':
                base_query = base_query.order_by(Product.price.desc())
            elif sort_by == 'name':
                base_query = base_query.order_by(Product.name.asc())
            elif sort_by == 'newest':
                base_query = base_query.order_by(Product.created_at.desc())
            else:  # relevance (par défaut)
                # Scoring simple: priorité au nom
                if query and query.strip():
                    base_query = base_query.order_by(
                        Product.name.ilike(f"%{query.strip()}%").desc(),
                        Product.created_at.desc()
                    )
            
            # Pagination
            pagination = base_query.paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )
            
            return {
                'success': True,
                'products': pagination.items,
                'total': pagination.total,
                'page': page,
                'per_page': per_page,
                'pages': pagination.pages,
                'has_prev': pagination.has_prev,
                'has_next': pagination.has_next
            }
            
        except Exception as e:
            logger.error(f"Erreur recherche produits: {e}")
            return {
                'success': False,
                'error': str(e),
                'products': [],
                'total': 0
            }
    
    def get_search_suggestions(self, query: str, limit: int = 5) -> List[str]:
        """
        Obtenir des suggestions de recherche
        
        Args:
            query: Début de la recherche
            limit: Nombre de suggestions
            
        Returns:
            Liste de suggestions
        """
        try:
            if not query or len(query) < 2:
                return []
            
            search_term = f"{query}%"
            
            # Rechercher dans les noms de produits
            products = Product.query.filter(
                Product.is_active == True,
                Product.name.ilike(search_term)
            ).limit(limit).all()
            
            suggestions = [p.name for p in products]
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Erreur suggestions recherche: {e}")
            return []
    
    def get_popular_searches(self, limit: int = 10) -> List[str]:
        """
        Obtenir les recherches populaires (à implémenter avec tracking)
        
        Args:
            limit: Nombre de résultats
            
        Returns:
            Liste de termes populaires
        """
        # TODO: Implémenter tracking des recherches
        # Pour l'instant, retourner les catégories populaires
        try:
            categories = Category.query.limit(limit).all()
            return [cat.name for cat in categories]
        except:
            return []
    
    def get_facets(self, query: Optional[str] = None, category_id: Optional[int] = None) -> Dict:
        """
        Obtenir les facettes de recherche (filtres disponibles)
        
        Args:
            query: Terme de recherche
            category_id: Catégorie
            
        Returns:
            dict: Facettes (prix, catégories, etc.)
        """
        try:
            # Base query
            base_query = Product.query.filter(Product.is_active == True)
            
            if query and query.strip():
                search_term = f"%{query.strip()}%"
                base_query = base_query.filter(
                    or_(
                        Product.name.ilike(search_term),
                        Product.description.ilike(search_term)
                    )
                )
            
            if category_id:
                base_query = base_query.filter(Product.category_id == category_id)
            
            # Prix min/max
            price_stats = db.session.query(
                func.min(Product.price).label('min_price'),
                func.max(Product.price).label('max_price')
            ).filter(Product.id.in_([p.id for p in base_query.all()])).first()
            
            # Catégories disponibles
            category_counts = db.session.query(
                Product.category_id,
                func.count(Product.id).label('count')
            ).filter(
                Product.id.in_([p.id for p in base_query.all()])
            ).group_by(Product.category_id).all()
            
            categories = []
            for cat_id, count in category_counts:
                if cat_id:
                    category = Category.query.get(cat_id)
                    if category:
                        categories.append({
                            'id': category.id,
                            'name': category.name,
                            'count': count
                        })
            
            return {
                'success': True,
                'price_range': {
                    'min': float(price_stats.min_price or 0),
                    'max': float(price_stats.max_price or 0)
                },
                'categories': categories
            }
            
        except Exception as e:
            logger.error(f"Erreur facettes recherche: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# Instance globale
_search_service = None

def get_search_service() -> SearchService:
    """Obtenir l'instance du service de recherche"""
    global _search_service
    
    if _search_service is None:
        _search_service = SearchService()
    
    return _search_service
