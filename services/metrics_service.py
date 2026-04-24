"""
Service de métriques et monitoring
Phase 4 - Monitoring avancé
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from extensions import db
from models.product import Product
from models.order import Order
from models.user import User
import time


class MetricsService:
    """Service pour collecter et analyser les métriques"""
    
    @staticmethod
    def get_system_metrics() -> Dict:
        """
        Obtenir les métriques système
        
        Returns:
            dict: Métriques système
        """
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'database': MetricsService._get_database_metrics(),
            'products': MetricsService._get_product_metrics(),
            'orders': MetricsService._get_order_metrics(),
            'users': MetricsService._get_user_metrics()
        }
    
    @staticmethod
    def _get_database_metrics() -> Dict:
        """Métriques base de données"""
        try:
            start = time.time()
            db.session.execute(db.text('SELECT 1'))
            query_time = (time.time() - start) * 1000  # ms
            
            return {
                'status': 'healthy',
                'query_time_ms': round(query_time, 2)
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    @staticmethod
    def _get_product_metrics() -> Dict:
        """Métriques produits"""
        try:
            total = Product.query.count()
            active = Product.query.filter(Product.is_active == True).count()
            out_of_stock = Product.query.filter(Product.stock_quantity == 0).count()
            
            return {
                'total': total,
                'active': active,
                'inactive': total - active,
                'out_of_stock': out_of_stock,
                'in_stock': active - out_of_stock
            }
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def _get_order_metrics() -> Dict:
        """Métriques commandes"""
        try:
            total = Order.query.count()
            
            # Commandes dernières 24h
            yesterday = datetime.utcnow() - timedelta(days=1)
            recent = Order.query.filter(Order.created_at >= yesterday).count()
            
            # Commandes par statut
            pending = Order.query.filter(Order.status == 'pending').count()
            completed = Order.query.filter(Order.status == 'completed').count()
            
            return {
                'total': total,
                'last_24h': recent,
                'pending': pending,
                'completed': completed
            }
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def _get_user_metrics() -> Dict:
        """Métriques utilisateurs"""
        try:
            total = User.query.count()
            
            # Utilisateurs actifs (derniers 30 jours)
            month_ago = datetime.utcnow() - timedelta(days=30)
            active = User.query.filter(User.last_login >= month_ago).count()
            
            return {
                'total': total,
                'active_30d': active
            }
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def get_performance_metrics() -> Dict:
        """
        Métriques de performance
        
        Returns:
            dict: Métriques de performance
        """
        metrics = {}
        
        # Test requête simple
        start = time.time()
        Product.query.limit(1).all()
        metrics['simple_query_ms'] = round((time.time() - start) * 1000, 2)
        
        # Test requête complexe
        start = time.time()
        Product.query.join(Product.category).filter(
            Product.is_active == True
        ).limit(10).all()
        metrics['complex_query_ms'] = round((time.time() - start) * 1000, 2)
        
        return metrics
    
    @staticmethod
    def get_health_status() -> Dict:
        """
        Vérifier l'état de santé du système
        
        Returns:
            dict: Statut de santé
        """
        health = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'checks': {}
        }
        
        # Check database
        try:
            db.session.execute(db.text('SELECT 1'))
            health['checks']['database'] = 'ok'
        except Exception as e:
            health['checks']['database'] = 'error'
            health['status'] = 'unhealthy'
        
        # Check products
        try:
            Product.query.limit(1).all()
            health['checks']['products'] = 'ok'
        except Exception as e:
            health['checks']['products'] = 'error'
            health['status'] = 'degraded'
        
        return health
    
    @staticmethod
    def get_sales_metrics(days: int = 30) -> Dict:
        """
        Métriques de ventes
        
        Args:
            days: Nombre de jours
            
        Returns:
            dict: Métriques de ventes
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            orders = Order.query.filter(
                Order.created_at >= start_date,
                Order.status == 'completed'
            ).all()
            
            total_revenue = sum(order.total_amount for order in orders)
            total_orders = len(orders)
            avg_order = total_revenue / total_orders if total_orders > 0 else 0
            
            return {
                'period_days': days,
                'total_orders': total_orders,
                'total_revenue': round(total_revenue, 2),
                'average_order_value': round(avg_order, 2)
            }
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def get_top_products(limit: int = 10) -> List[Dict]:
        """
        Produits les plus vendus
        
        Args:
            limit: Nombre de produits
            
        Returns:
            list: Top produits
        """
        try:
            # Cette requête nécessiterait une table order_items
            # Pour l'instant, retourner les produits les plus récents
            products = Product.query.filter(
                Product.is_active == True
            ).order_by(Product.created_at.desc()).limit(limit).all()
            
            return [{
                'id': p.id,
                'name': p.name,
                'price': p.price,
                'stock': p.stock_quantity
            } for p in products]
        except Exception as e:
            return []


def get_metrics_service() -> MetricsService:
    """Obtenir instance du service de métriques"""
    return MetricsService()
