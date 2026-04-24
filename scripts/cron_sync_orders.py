"""
CRON Job - Synchronisation Statuts Commandes CJ
Exécution horaire (toutes les heures)
Met à jour les statuts des commandes CJ depuis l'API
"""
import sys
import os
from datetime import datetime, timedelta
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from models.order import Order
from models.api_provider import ApiProvider
from services.api_providers.cj_dropshipping_optimized import CJDropshippingProvider
from services.admin_notifications import AdminNotificationService
from extensions import db
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def sync_order_status(cj_api, order):
    """
    Synchroniser le statut d'une commande depuis CJ
    
    Args:
        cj_api: Instance CJDropshippingProvider
        order: Commande à synchroniser
        
    Returns:
        dict: Résultat de la synchronisation
    """
    try:
        if not order.cj_order_id:
            return {'success': False, 'error': 'Pas de cj_order_id'}
        
        # Récupérer le statut depuis CJ
        result = cj_api.get_order_status(order.cj_order_id)
        
        if not result.get('success'):
            return {'success': False, 'error': result.get('error')}
        
        order_data = result.get('data', {})
        cj_status = order_data.get('orderStatus')
        tracking_number = order_data.get('trackingNumber')
        logistics_name = order_data.get('logisticName')
        
        old_status = order.status
        status_changed = False
        
        # Mapper le statut CJ vers le statut local
        if cj_status == 'SHIPPED' and order.status != 'shipped':
            order.status = 'shipped'
            order.cj_status = 'SHIPPED'
            order.cj_tracking_number = tracking_number
            order.cj_logistics_name = logistics_name
            order.shipped_at = datetime.now()
            status_changed = True
            
            # Envoyer email au client
            try:
                from services.webhook_handler import WebhookHandler
                handler = WebhookHandler()
                handler._send_shipping_notification(order)
            except Exception as e:
                logger.warning(f"Erreur envoi email expédition: {e}")
        
        elif cj_status == 'DELIVERED' and order.status != 'delivered':
            order.status = 'delivered'
            order.cj_status = 'DELIVERED'
            order.delivered_at = datetime.now()
            status_changed = True
            
            # Envoyer email au client
            try:
                from services.webhook_handler import WebhookHandler
                handler = WebhookHandler()
                handler._send_delivery_notification(order)
            except Exception as e:
                logger.warning(f"Erreur envoi email livraison: {e}")
        
        elif cj_status == 'CANCELLED' and order.status != 'cancelled':
            order.status = 'cancelled'
            order.cj_status = 'CANCELLED'
            order.cancelled_at = datetime.now()
            status_changed = True
            
            # Envoyer email au client
            try:
                from services.webhook_handler import WebhookHandler
                handler = WebhookHandler()
                handler._send_cancellation_notification(order, 'Annulée par CJ')
            except Exception as e:
                logger.warning(f"Erreur envoi email annulation: {e}")
        
        elif cj_status == 'PROCESSING' and order.status == 'pending':
            order.status = 'processing'
            order.cj_status = 'PROCESSING'
            status_changed = True
        
        # Mettre à jour tracking si fourni
        if tracking_number and tracking_number != order.cj_tracking_number:
            order.cj_tracking_number = tracking_number
            status_changed = True
        
        if logistics_name and logistics_name != order.cj_logistics_name:
            order.cj_logistics_name = logistics_name
            status_changed = True
        
        if status_changed:
            db.session.commit()
            return {
                'success': True,
                'changed': True,
                'old_status': old_status,
                'new_status': order.status
            }
        else:
            return {
                'success': True,
                'changed': False,
                'status': order.status
            }
            
    except Exception as e:
        logger.error(f"Erreur sync commande {order.order_number}: {e}")
        db.session.rollback()
        return {'success': False, 'error': str(e)}


def sync_all_orders(max_orders=50):
    """
    Synchroniser les statuts des commandes CJ actives
    
    Args:
        max_orders: Nombre max de commandes à synchroniser (défaut: 10)
    """
    
    with app.app_context():
        logger.info("="*70)
        logger.info("🔄 SYNCHRONISATION STATUTS COMMANDES CJ")
        logger.info("="*70)
        logger.info(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Limite: {max_orders} commandes")
        
        # Récupérer le provider CJ
        provider = ApiProvider.query.filter_by(name='CJ Dropshipping').first()
        
        if not provider:
            logger.error("❌ Provider CJ Dropshipping non trouvé")
            return False
        
        logger.info(f"✅ Provider: {provider.name}")
        
        # Créer l'instance API
        cj_api = CJDropshippingProvider(provider)
        
        # Récupérer les commandes CJ non terminées (pas delivered/cancelled)
        # Synchroniser les commandes des 30 derniers jours
        cutoff_date = datetime.now() - timedelta(days=30)
        
        orders = Order.query.filter(
            Order.cj_order_id.isnot(None),
            Order.cj_order_id != '',
            Order.status.in_(['pending', 'processing', 'shipped']),
            Order.created_at >= cutoff_date
        ).limit(max_orders).all()
        
        total_orders = len(orders)
        logger.info(f"\n📦 Commandes à synchroniser: {total_orders}")
        
        if total_orders == 0:
            logger.info("✅ Aucune commande à synchroniser")
            return True
        
        # Statistiques
        success_count = 0
        error_count = 0
        changed_count = 0
        
        # Synchroniser chaque commande
        for i, order in enumerate(orders, 1):
            logger.info(f"\n[{i}/{total_orders}] Commande: {order.order_number}")
            logger.info(f"  CJ Order ID: {order.cj_order_id}")
            logger.info(f"  Statut actuel: {order.status}")
            
            # Délai pour éviter rate limiting
            if i > 1:
                time.sleep(0.5)
            
            result = sync_order_status(cj_api, order)
            
            if result.get('success'):
                success_count += 1
                if result.get('changed'):
                    changed_count += 1
                    logger.info(f"  ✅ Statut mis à jour: {result.get('old_status')} → {result.get('new_status')}")
                else:
                    logger.info(f"  ℹ️ Pas de changement")
            else:
                error_count += 1
                logger.error(f"  ❌ Erreur: {result.get('error')}")
        
        # Résumé
        logger.info("\n" + "="*70)
        logger.info("📊 RÉSUMÉ DE LA SYNCHRONISATION")
        logger.info("="*70)
        logger.info(f"Total commandes: {total_orders}")
        logger.info(f"✅ Succès: {success_count}")
        logger.info(f"🔄 Changements: {changed_count}")
        logger.info(f"❌ Erreurs: {error_count}")
        logger.info(f"Taux de réussite: {(success_count/total_orders*100):.1f}%")
        logger.info("="*70)
        
        return error_count == 0


if __name__ == '__main__':
    try:
        success = sync_all_orders()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
