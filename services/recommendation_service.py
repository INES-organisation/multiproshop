"""
Service de recommandations de produits
Phase 3.3 - Algorithmes de recommandation
"""
from typing import List, Optional, Dict
from sqlalchemy import func, and_, or_
from models.product import Product
from models.order import Order, OrderItem
from models.category import Category
from extensions import db, cache
import logging
import random

logger = logging.getLogger(__name__)


class RecommendationService:
    """Service de recommandations de produits"""
    
    def __init__(self):
        """Initialiser le service"""
        pass
    
    def get_similar_products(
        self,
        product_id: int,
        limit: int = 6
    ) -> List[Product]:
        """
        Obtenir des produits similaires
        
        Args:
            product_id: ID du produit de référence
            limit: Nombre de produits à retourner
            
        Returns:
            Liste de produits similaires
        """
        try:
            # Récupérer le produit de référence
            product = Product.query.get(product_id)
            if not product:
                return []
            
            # Clé de cache
            cache_key = f"similar_products:{product_id}:{limit}"
            cached = cache.get(cache_key)
            if cached:
                return cached
            
            # Rechercher des produits similaires
            similar = Product.query.filter(
                Product.id != product_id,
                Product.is_active == True,
                or_(
                    # Même catégorie
                    Product.category_id == product.category_id,
                    # Prix similaire (+/- 30%)
                    and_(
                        Product.price >= product.price * 0.7,
                        Product.price <= product.price * 1.3
                    )
                )
            ).limit(limit * 2).all()
            
            # Scorer les produits
            scored_products = []
            for p in similar:
                score = 0
                
                # Même catégorie = +10 points
                if p.category_id == product.category_id:
                    score += 10
                
                # Prix similaire = +5 points
                price_diff = abs(p.price - product.price) / product.price
                if price_diff < 0.1:
                    score += 5
                elif price_diff < 0.3:
                    score += 3
                
                # En stock = +2 points
                if p.stock > 0:
                    score += 2
                
                # Produit CJ = +1 point
                if p.cj_pid:
                    score += 1
                
                scored_products.append((p, score))
            
            # Trier par score et prendre les meilleurs
            scored_products.sort(key=lambda x: x[1], reverse=True)
            results = [p for p, score in scored_products[:limit]]
            
            # Mettre en cache (1 heure)
            cache.set(cache_key, results, timeout=3600)
            
            return results
            
        except Exception as e:
            logger.error(f"Erreur produits similaires: {e}")
            return []
    
    def get_frequently_bought_together(
        self,
        product_id: int,
        limit: int = 4
    ) -> List[Product]:
        """
        Obtenir les produits fréquemment achetés ensemble
        
        Args:
            product_id: ID du produit de référence
            limit: Nombre de produits à retourner
            
        Returns:
            Liste de produits
        """
        try:
            # Clé de cache
            cache_key = f"bought_together:{product_id}:{limit}"
            cached = cache.get(cache_key)
            if cached:
                return cached
            
            # Trouver les commandes contenant ce produit
            orders_with_product = db.session.query(Order.id).join(
                OrderItem
            ).filter(
                OrderItem.product_id == product_id,
                Order.payment_status == 'paid'
            ).subquery()
            
            # Trouver les autres produits dans ces commandes
            frequently_bought = db.session.query(
                Product,
                func.count(OrderItem.id).label('frequency')
            ).join(
                OrderItem, OrderItem.product_id == Product.id
            ).join(
                Order, Order.id == OrderItem.order_id
            ).filter(
                Order.id.in_(orders_with_product),
                Product.id != product_id,
                Product.is_active == True
            ).group_by(
                Product.id
            ).order_by(
                func.count(OrderItem.id).desc()
            ).limit(limit).all()
            
            results = [product for product, freq in frequently_bought]
            
            # Si pas assez de résultats, compléter avec des produits similaires
            if len(results) < limit:
                similar = self.get_similar_products(product_id, limit - len(results))
                results.extend(similar)
            
            # Mettre en cache (2 heures)
            cache.set(cache_key, results, timeout=7200)
            
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Erreur produits achetés ensemble: {e}")
            # Fallback: produits similaires
            return self.get_similar_products(product_id, limit)
    
    def get_trending_products(
        self,
        limit: int = 8,
        days: int = 7
    ) -> List[Product]:
        """
        Obtenir les produits tendance
        
        Args:
            limit: Nombre de produits
            days: Période en jours
            
        Returns:
            Liste de produits tendance
        """
        try:
            from datetime import datetime, timedelta
            
            # Clé de cache
            cache_key = f"trending_products:{limit}:{days}"
            cached = cache.get(cache_key)
            if cached:
                return cached
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Produits les plus vendus récemment
            trending = db.session.query(
                Product,
                func.count(OrderItem.id).label('sales_count'),
                func.sum(OrderItem.quantity).label('total_quantity')
            ).join(
                OrderItem, OrderItem.product_id == Product.id
            ).join(
                Order, Order.id == OrderItem.order_id
            ).filter(
                Product.is_active == True,
                Order.payment_status == 'paid',
                Order.created_at >= cutoff_date
            ).group_by(
                Product.id
            ).order_by(
                func.sum(OrderItem.quantity).desc()
            ).limit(limit).all()
            
            results = [product for product, sales, qty in trending]
            
            # Si pas assez de résultats, ajouter des produits récents
            if len(results) < limit:
                recent = Product.query.filter(
                    Product.is_active == True,
                    Product.id.notin_([p.id for p in results])
                ).order_by(
                    Product.created_at.desc()
                ).limit(limit - len(results)).all()
                results.extend(recent)
            
            # Mettre en cache (30 minutes)
            cache.set(cache_key, results, timeout=1800)
            
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Erreur produits tendance: {e}")
            # Fallback: produits récents
            return Product.query.filter(
                Product.is_active == True
            ).order_by(
                Product.created_at.desc()
            ).limit(limit).all()
    
    def get_personalized_recommendations(
        self,
        user_id: Optional[int] = None,
        limit: int = 8
    ) -> List[Product]:
        """
        Obtenir des recommandations personnalisées
        
        Args:
            user_id: ID de l'utilisateur (optionnel)
            limit: Nombre de produits
            
        Returns:
            Liste de produits recommandés
        """
        try:
            if user_id:
                # Clé de cache
                cache_key = f"personalized:{user_id}:{limit}"
                cached = cache.get(cache_key)
                if cached:
                    return cached
                
                # Récupérer les catégories préférées de l'utilisateur
                favorite_categories = db.session.query(
                    Product.category_id,
                    func.count(OrderItem.id).label('count')
                ).join(
                    OrderItem, OrderItem.product_id == Product.id
                ).join(
                    Order, Order.id == OrderItem.order_id
                ).filter(
                    Order.user_id == user_id,
                    Order.payment_status == 'paid'
                ).group_by(
                    Product.category_id
                ).order_by(
                    func.count(OrderItem.id).desc()
                ).limit(3).all()
                
                if favorite_categories:
                    category_ids = [cat_id for cat_id, count in favorite_categories]
                    
                    # Recommander des produits de ces catégories
                    recommendations = Product.query.filter(
                        Product.is_active == True,
                        Product.category_id.in_(category_ids),
                        Product.stock > 0
                    ).order_by(
                        func.random()
                    ).limit(limit).all()
                    
                    # Mettre en cache (1 heure)
                    cache.set(cache_key, recommendations, timeout=3600)
                    
                    return recommendations
            
            # Fallback: produits tendance
            return self.get_trending_products(limit=limit)
            
        except Exception as e:
            logger.error(f"Erreur recommandations personnalisées: {e}")
            return self.get_trending_products(limit=limit)
    
    def get_new_arrivals(self, limit: int = 8) -> List[Product]:
        """
        Obtenir les nouveautés
        
        Args:
            limit: Nombre de produits
            
        Returns:
            Liste de nouveaux produits
        """
        try:
            # Clé de cache
            cache_key = f"new_arrivals:{limit}"
            cached = cache.get(cache_key)
            if cached:
                return cached
            
            new_products = Product.query.filter(
                Product.is_active == True
            ).order_by(
                Product.created_at.desc()
            ).limit(limit).all()
            
            # Mettre en cache (15 minutes)
            cache.set(cache_key, new_products, timeout=900)
            
            return new_products
            
        except Exception as e:
            logger.error(f"Erreur nouveautés: {e}")
            return []


# Instance globale
_recommendation_service = None

def get_recommendation_service() -> RecommendationService:
    """Obtenir l'instance du service de recommandations"""
    global _recommendation_service
    
    if _recommendation_service is None:
        _recommendation_service = RecommendationService()
    
    return _recommendation_service
