"""
Service d'analytics pour CJ Dropshipping
Phase 2.2 - Dashboard Admin avec KPIs et statistiques
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
from extensions import db
from models.order import Order, OrderItem
from models.product import Product
from models.product_variant import ProductVariant

logger = logging.getLogger(__name__)


class CjAnalyticsService:
    """Service pour les analytics CJ Dropshipping"""
    
    def get_dashboard_kpis(self, days: int = 30) -> Dict:
        """
        Récupérer les KPIs principaux du dashboard
        
        Args:
            days: Nombre de jours à analyser
            
        Returns:
            dict: KPIs (ventes, commandes, revenus, marge)
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Commandes CJ payées
            cj_orders = Order.query.filter(
                Order.cj_order_id.isnot(None),
                Order.cj_order_id != '',
                Order.payment_status == 'paid',
                Order.created_at >= cutoff_date
            ).all()
            
            total_orders = len(cj_orders)
            total_revenue = sum(order.total for order in cj_orders)
            
            # Calculer la marge (prix de vente - coût CJ)
            total_cost = 0
            total_margin = 0
            
            for order in cj_orders:
                for item in order.items:
                    if item.product and item.product.cj_price:
                        cost = item.product.cj_price * item.quantity
                        revenue = item.price * item.quantity
                        total_cost += cost
                        total_margin += (revenue - cost)
            
            margin_percentage = (total_margin / total_revenue * 100) if total_revenue > 0 else 0
            
            # Commandes par statut
            status_counts = {}
            for order in cj_orders:
                status = order.status
                status_counts[status] = status_counts.get(status, 0) + 1
            
            return {
                'success': True,
                'period_days': days,
                'total_orders': total_orders,
                'total_revenue': round(total_revenue, 2),
                'total_cost': round(total_cost, 2),
                'total_margin': round(total_margin, 2),
                'margin_percentage': round(margin_percentage, 2),
                'average_order_value': round(total_revenue / total_orders, 2) if total_orders > 0 else 0,
                'status_counts': status_counts
            }
            
        except Exception as e:
            logger.error(f"Erreur récupération KPIs: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_sales_evolution(self, days: int = 30) -> Dict:
        """
        Récupérer l'évolution des ventes sur N jours
        
        Args:
            days: Nombre de jours
            
        Returns:
            dict: Données pour graphique (dates, ventes)
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Grouper les commandes par jour
            daily_sales = db.session.query(
                func.date(Order.created_at).label('date'),
                func.count(Order.id).label('orders'),
                func.sum(Order.total).label('revenue')
            ).filter(
                Order.cj_order_id.isnot(None),
                Order.cj_order_id != '',
                Order.payment_status == 'paid',
                Order.created_at >= cutoff_date
            ).group_by(
                func.date(Order.created_at)
            ).order_by('date').all()
            
            # Formater pour le graphique
            dates = []
            orders = []
            revenues = []
            
            for row in daily_sales:
                dates.append(row.date.strftime('%Y-%m-%d'))
                orders.append(row.orders)
                revenues.append(float(row.revenue or 0))
            
            return {
                'success': True,
                'dates': dates,
                'orders': orders,
                'revenues': revenues
            }
            
        except Exception as e:
            logger.error(f"Erreur évolution ventes: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_top_products(self, limit: int = 10, days: int = 30) -> Dict:
        """
        Récupérer les produits les plus vendus
        
        Args:
            limit: Nombre de produits à retourner
            days: Période en jours
            
        Returns:
            dict: Top produits avec quantités et revenus
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Grouper par produit
            top_products = db.session.query(
                Product.id,
                Product.name,
                Product.image_url,
                func.sum(OrderItem.quantity).label('total_quantity'),
                func.sum(OrderItem.price * OrderItem.quantity).label('total_revenue'),
                func.count(OrderItem.id).label('order_count')
            ).join(
                OrderItem, OrderItem.product_id == Product.id
            ).join(
                Order, Order.id == OrderItem.order_id
            ).filter(
                Product.cj_pid.isnot(None),
                Product.cj_pid != '',
                Order.payment_status == 'paid',
                Order.created_at >= cutoff_date
            ).group_by(
                Product.id
            ).order_by(
                func.sum(OrderItem.quantity).desc()
            ).limit(limit).all()
            
            products = []
            for row in top_products:
                products.append({
                    'id': row.id,
                    'name': row.name,
                    'image_url': row.image_url,
                    'quantity': row.total_quantity,
                    'revenue': round(float(row.total_revenue or 0), 2),
                    'order_count': row.order_count
                })
            
            return {
                'success': True,
                'products': products
            }
            
        except Exception as e:
            logger.error(f"Erreur top produits: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_category_stats(self, days: int = 30) -> Dict:
        """
        Récupérer les statistiques par catégorie
        
        Args:
            days: Période en jours
            
        Returns:
            dict: Stats par catégorie
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Grouper par catégorie
            category_stats = db.session.query(
                Product.category_id,
                func.count(OrderItem.id).label('order_count'),
                func.sum(OrderItem.quantity).label('total_quantity'),
                func.sum(OrderItem.price * OrderItem.quantity).label('total_revenue')
            ).join(
                OrderItem, OrderItem.product_id == Product.id
            ).join(
                Order, Order.id == OrderItem.order_id
            ).filter(
                Product.cj_pid.isnot(None),
                Product.cj_pid != '',
                Order.payment_status == 'paid',
                Order.created_at >= cutoff_date
            ).group_by(
                Product.category_id
            ).all()
            
            categories = []
            for row in category_stats:
                if row.category_id:
                    from models.category import Category
                    category = Category.query.get(row.category_id)
                    if category:
                        categories.append({
                            'id': category.id,
                            'name': category.name,
                            'order_count': row.order_count,
                            'quantity': row.total_quantity,
                            'revenue': round(float(row.total_revenue or 0), 2)
                        })
            
            return {
                'success': True,
                'categories': categories
            }
            
        except Exception as e:
            logger.error(f"Erreur stats catégories: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_alerts(self) -> Dict:
        """
        Récupérer les alertes importantes
        
        Returns:
            dict: Liste des alertes
        """
        try:
            alerts = []
            
            # Alerte 1: Produits en rupture de stock
            out_of_stock = Product.query.filter(
                Product.cj_pid.isnot(None),
                Product.cj_pid != '',
                Product.is_active == True,
                Product.stock <= 0
            ).count()
            
            if out_of_stock > 0:
                alerts.append({
                    'type': 'warning',
                    'title': 'Produits en rupture',
                    'message': f'{out_of_stock} produit(s) CJ en rupture de stock',
                    'count': out_of_stock
                })
            
            # Alerte 2: Stock faible (<10)
            low_stock = Product.query.filter(
                Product.cj_pid.isnot(None),
                Product.cj_pid != '',
                Product.is_active == True,
                Product.stock > 0,
                Product.stock < 10
            ).count()
            
            if low_stock > 0:
                alerts.append({
                    'type': 'info',
                    'title': 'Stock faible',
                    'message': f'{low_stock} produit(s) avec stock < 10',
                    'count': low_stock
                })
            
            # Alerte 3: Commandes en attente
            pending_orders = Order.query.filter(
                Order.cj_order_id.isnot(None),
                Order.cj_order_id != '',
                Order.status == 'pending'
            ).count()
            
            if pending_orders > 0:
                alerts.append({
                    'type': 'warning',
                    'title': 'Commandes en attente',
                    'message': f'{pending_orders} commande(s) en attente de traitement',
                    'count': pending_orders
                })
            
            # Alerte 4: Produits sans prix CJ
            no_price = Product.query.filter(
                Product.cj_pid.isnot(None),
                Product.cj_pid != '',
                or_(Product.cj_price.is_(None), Product.cj_price == 0)
            ).count()
            
            if no_price > 0:
                alerts.append({
                    'type': 'danger',
                    'title': 'Produits sans prix CJ',
                    'message': f'{no_price} produit(s) sans prix CJ défini',
                    'count': no_price
                })
            
            return {
                'success': True,
                'alerts': alerts,
                'total_alerts': len(alerts)
            }
            
        except Exception as e:
            logger.error(f"Erreur récupération alertes: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_product_stats(self) -> Dict:
        """
        Récupérer les statistiques globales des produits CJ
        
        Returns:
            dict: Stats produits
        """
        try:
            total_products = Product.query.filter(
                Product.cj_pid.isnot(None),
                Product.cj_pid != ''
            ).count()
            
            active_products = Product.query.filter(
                Product.cj_pid.isnot(None),
                Product.cj_pid != '',
                Product.is_active == True
            ).count()
            
            in_stock = Product.query.filter(
                Product.cj_pid.isnot(None),
                Product.cj_pid != '',
                Product.stock > 0
            ).count()
            
            total_variants = ProductVariant.query.join(
                Product, Product.id == ProductVariant.product_id
            ).filter(
                Product.cj_pid.isnot(None),
                Product.cj_pid != ''
            ).count()
            
            return {
                'success': True,
                'total_products': total_products,
                'active_products': active_products,
                'inactive_products': total_products - active_products,
                'in_stock': in_stock,
                'out_of_stock': total_products - in_stock,
                'total_variants': total_variants
            }
            
        except Exception as e:
            logger.error(f"Erreur stats produits: {e}")
            return {'success': False, 'error': str(e)}
