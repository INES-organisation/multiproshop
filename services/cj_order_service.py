"""
Service de gestion des commandes CJ Dropshipping
Phase 1.2 - Création et suivi des commandes sur CJ après paiement
"""
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from extensions import db
from models.order import Order, OrderItem
from models.product import Product
from models.product_variant import ProductVariant

logger = logging.getLogger(__name__)


class CjOrderService:
    """Service pour gérer les commandes CJ Dropshipping"""
    
    def __init__(self, cj_api):
        """
        Initialiser le service
        
        Args:
            cj_api: Instance de CJDropshippingProvider
        """
        self.cj_api = cj_api
    
    def create_cj_order(self, order_id: int) -> Dict:
        """
        Créer une commande sur CJ après paiement réussi
        
        Args:
            order_id: ID de la commande locale
            
        Returns:
            dict: Résultat de la création
        """
        try:
            order = Order.query.get(order_id)
            
            if not order:
                return {
                    'success': False,
                    'message': 'Commande introuvable'
                }
            
            # Vérifier que la commande est payée
            if order.payment_status != 'paid':
                return {
                    'success': False,
                    'message': 'Commande non payée'
                }
            
            # Vérifier si déjà créée sur CJ
            if hasattr(order, 'cj_order_id') and order.cj_order_id:
                return {
                    'success': False,
                    'message': 'Commande déjà créée sur CJ',
                    'cj_order_id': order.cj_order_id
                }
            
            # Préparer les données de la commande
            order_data = self._prepare_order_data(order)
            
            if not order_data:
                return {
                    'success': False,
                    'message': 'Impossible de préparer les données de commande'
                }
            
            # Appel API CJ pour créer la commande
            response = self.cj_api._make_request('POST', '/shopping/order/createOrder', order_data)
            
            if not response or response.get('code') != 200:
                error_msg = response.get('message', 'Erreur API CJ') if response else 'Pas de réponse API'
                logger.error(f"[CjOrderService] Erreur création commande CJ: {error_msg}")
                
                return {
                    'success': False,
                    'message': f'Erreur CJ: {error_msg}',
                    'response': response
                }
            
            # Récupérer l'ID de commande CJ
            cj_data = response.get('data', {})
            cj_order_id = cj_data.get('orderId') or cj_data.get('orderNum')
            
            if not cj_order_id:
                return {
                    'success': False,
                    'message': 'ID commande CJ non reçu',
                    'response': response
                }
            
            # Mettre à jour la commande locale
            if not hasattr(order, 'cj_order_id'):
                # Le champ n'existe pas encore, on le stocke dans admin_notes temporairement
                order.admin_notes = f"CJ Order ID: {cj_order_id}\n{order.admin_notes or ''}"
            else:
                order.cj_order_id = cj_order_id
            
            order.status = 'processing'
            db.session.commit()
            
            logger.info(f"[CjOrderService] Commande CJ créée: {cj_order_id} pour Order #{order.order_number}")
            
            # Confirmer automatiquement la commande CJ
            confirm_result = self.confirm_cj_order(cj_order_id)
            
            return {
                'success': True,
                'message': 'Commande CJ créée avec succès',
                'cj_order_id': cj_order_id,
                'order_number': order.order_number,
                'confirmed': confirm_result.get('success', False)
            }
            
        except Exception as e:
            logger.error(f"[CjOrderService] Exception create_cj_order: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                'success': False,
                'message': f'Exception: {str(e)}'
            }
    
    def _prepare_order_data(self, order: Order) -> Optional[Dict]:
        """
        Préparer les données de commande pour l'API CJ
        
        Args:
            order: Instance Order
            
        Returns:
            dict: Données formatées pour CJ ou None
        """
        try:
            # Préparer la liste des produits
            products = []
            
            for item in order.order_items:
                product = item.product
                
                if not product or not product.cj_pid:
                    logger.warning(f"[CjOrderService] Produit {item.product_id} n'est pas un produit CJ")
                    continue
                
                product_data = {
                    'pid': product.cj_pid,
                    'quantity': item.quantity
                }
                
                # Ajouter la variante si disponible
                if hasattr(item, 'variant_id') and item.variant_id:
                    variant = ProductVariant.query.get(item.variant_id)
                    if variant and variant.cj_vid:
                        product_data['vid'] = variant.cj_vid
                
                products.append(product_data)
            
            if not products:
                logger.error("[CjOrderService] Aucun produit CJ dans la commande")
                return None
            
            # Préparer l'adresse de livraison
            shipping_address = {
                'firstName': order.shipping_first_name,
                'lastName': order.shipping_last_name,
                'address': order.shipping_address,
                'city': order.shipping_city,
                'zip': order.shipping_postal_code,
                'countryCode': order.shipping_country,
                'phone': order.customer_phone or '',
                'email': order.customer_email
            }
            
            # Données de la commande
            order_data = {
                'orderNumber': order.order_number,  # Notre numéro de commande
                'shippingAddress': shipping_address,
                'products': products,
                'remark': order.customer_notes or ''
            }
            
            # Ajouter la méthode de livraison si disponible
            if order.shipping_method:
                order_data['logisticsName'] = order.shipping_method
            
            return order_data
            
        except Exception as e:
            logger.error(f"[CjOrderService] Erreur _prepare_order_data: {e}")
            return None
    
    def confirm_cj_order(self, cj_order_id: str) -> Dict:
        """
        Confirmer une commande CJ (nécessaire après création)
        
        Args:
            cj_order_id: ID de la commande CJ
            
        Returns:
            dict: Résultat de la confirmation
        """
        try:
            response = self.cj_api._make_request('POST', '/shopping/order/confirmOrder', {
                'orderId': cj_order_id
            })
            
            if response and response.get('code') == 200:
                logger.info(f"[CjOrderService] Commande CJ confirmée: {cj_order_id}")
                
                return {
                    'success': True,
                    'message': 'Commande confirmée',
                    'cj_order_id': cj_order_id
                }
            else:
                error_msg = response.get('message', 'Erreur confirmation') if response else 'Pas de réponse'
                logger.error(f"[CjOrderService] Erreur confirmation: {error_msg}")
                
                return {
                    'success': False,
                    'message': error_msg
                }
                
        except Exception as e:
            logger.error(f"[CjOrderService] Exception confirm_cj_order: {e}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def get_order_status(self, cj_order_id: str) -> Dict:
        """
        Récupérer le statut d'une commande CJ
        
        Args:
            cj_order_id: ID de la commande CJ
            
        Returns:
            dict: Informations de statut
        """
        try:
            response = self.cj_api._make_request('POST', '/shopping/order/query', {
                'orderId': cj_order_id
            })
            
            if not response or response.get('code') != 200:
                return {
                    'success': False,
                    'message': 'Erreur récupération statut'
                }
            
            data = response.get('data', {})
            
            return {
                'success': True,
                'cj_order_id': cj_order_id,
                'status': data.get('orderStatus'),
                'tracking_number': data.get('trackingNumber'),
                'logistics_name': data.get('logisticsName'),
                'created_at': data.get('createTime'),
                'shipped_at': data.get('shippedTime'),
                'raw_data': data
            }
            
        except Exception as e:
            logger.error(f"[CjOrderService] Exception get_order_status: {e}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def get_tracking_info(self, cj_order_id: str) -> Dict:
        """
        Récupérer les informations de tracking d'une commande
        
        Args:
            cj_order_id: ID de la commande CJ
            
        Returns:
            dict: Informations de tracking
        """
        try:
            response = self.cj_api._make_request('POST', '/shopping/order/getTrackingNumber', {
                'orderId': cj_order_id
            })
            
            if not response or response.get('code') != 200:
                return {
                    'success': False,
                    'message': 'Tracking non disponible'
                }
            
            data = response.get('data', {})
            
            return {
                'success': True,
                'cj_order_id': cj_order_id,
                'tracking_number': data.get('trackingNumber'),
                'logistics_name': data.get('logisticsName'),
                'logistics_url': data.get('trackingUrl'),
                'shipped_at': data.get('shippedTime')
            }
            
        except Exception as e:
            logger.error(f"[CjOrderService] Exception get_tracking_info: {e}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def sync_order_status(self, order_id: int) -> Dict:
        """
        Synchroniser le statut d'une commande depuis CJ
        
        Args:
            order_id: ID de la commande locale
            
        Returns:
            dict: Résultat de la synchronisation
        """
        try:
            order = Order.query.get(order_id)
            
            if not order:
                return {
                    'success': False,
                    'message': 'Commande introuvable'
                }
            
            # Récupérer l'ID CJ
            cj_order_id = None
            if hasattr(order, 'cj_order_id'):
                cj_order_id = order.cj_order_id
            elif order.admin_notes and 'CJ Order ID:' in order.admin_notes:
                # Extraire depuis admin_notes si pas de champ dédié
                import re
                match = re.search(r'CJ Order ID: (\S+)', order.admin_notes)
                if match:
                    cj_order_id = match.group(1)
            
            if not cj_order_id:
                return {
                    'success': False,
                    'message': 'Pas de commande CJ associée'
                }
            
            # Récupérer le statut depuis CJ
            status_info = self.get_order_status(cj_order_id)
            
            if not status_info.get('success'):
                return status_info
            
            # Mapper les statuts CJ vers nos statuts
            cj_status = status_info.get('status', '')
            local_status = self._map_cj_status(cj_status)
            
            # Mettre à jour la commande locale
            old_status = order.status
            order.status = local_status
            
            # Mettre à jour le tracking si disponible
            tracking_number = status_info.get('tracking_number')
            if tracking_number:
                if hasattr(order, 'cj_tracking_number'):
                    order.cj_tracking_number = tracking_number
                else:
                    # Ajouter aux notes si pas de champ dédié
                    if 'Tracking:' not in (order.admin_notes or ''):
                        order.admin_notes = f"Tracking: {tracking_number}\n{order.admin_notes or ''}"
                
                # Mettre à jour shipped_at si expédié
                if local_status == 'shipped' and not order.shipped_at:
                    order.shipped_at = datetime.utcnow()
            
            # Mettre à jour delivered_at si livré
            if local_status == 'delivered' and not order.delivered_at:
                order.delivered_at = datetime.utcnow()
            
            db.session.commit()
            
            logger.info(f"[CjOrderService] Statut synchronisé: {old_status} → {local_status} pour Order #{order.order_number}")
            
            return {
                'success': True,
                'message': 'Statut synchronisé',
                'old_status': old_status,
                'new_status': local_status,
                'cj_status': cj_status,
                'tracking_number': tracking_number
            }
            
        except Exception as e:
            logger.error(f"[CjOrderService] Exception sync_order_status: {e}")
            db.session.rollback()
            return {
                'success': False,
                'message': str(e)
            }
    
    def _map_cj_status(self, cj_status: str) -> str:
        """
        Mapper les statuts CJ vers nos statuts locaux
        
        Args:
            cj_status: Statut CJ
            
        Returns:
            str: Statut local
        """
        status_mapping = {
            'PENDING': 'pending',
            'PAID': 'paid',
            'PROCESSING': 'processing',
            'SHIPPED': 'shipped',
            'DELIVERED': 'delivered',
            'CANCELLED': 'cancelled',
            'REFUNDED': 'cancelled'
        }
        
        return status_mapping.get(cj_status.upper(), 'processing')
    
    def cancel_cj_order(self, cj_order_id: str, reason: str = '') -> Dict:
        """
        Annuler une commande CJ
        
        Args:
            cj_order_id: ID de la commande CJ
            reason: Raison de l'annulation
            
        Returns:
            dict: Résultat de l'annulation
        """
        try:
            response = self.cj_api._make_request('POST', '/shopping/order/cancelOrder', {
                'orderId': cj_order_id,
                'reason': reason or 'Customer request'
            })
            
            if response and response.get('code') == 200:
                logger.info(f"[CjOrderService] Commande CJ annulée: {cj_order_id}")
                
                return {
                    'success': True,
                    'message': 'Commande annulée',
                    'cj_order_id': cj_order_id
                }
            else:
                error_msg = response.get('message', 'Erreur annulation') if response else 'Pas de réponse'
                
                return {
                    'success': False,
                    'message': error_msg
                }
                
        except Exception as e:
            logger.error(f"[CjOrderService] Exception cancel_cj_order: {e}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def sync_all_pending_orders(self) -> Dict:
        """
        Synchroniser toutes les commandes en attente
        
        Returns:
            dict: Résultat de la synchronisation
        """
        try:
            # Récupérer les commandes payées mais pas encore sur CJ
            orders = Order.query.filter(
                Order.payment_status == 'paid',
                Order.status.in_(['paid', 'processing'])
            ).all()
            
            results = {
                'total': len(orders),
                'created': 0,
                'synced': 0,
                'errors': 0,
                'details': []
            }
            
            for order in orders:
                # Vérifier si déjà sur CJ
                has_cj_order = False
                if hasattr(order, 'cj_order_id') and order.cj_order_id:
                    has_cj_order = True
                elif order.admin_notes and 'CJ Order ID:' in order.admin_notes:
                    has_cj_order = True
                
                if not has_cj_order:
                    # Créer sur CJ
                    result = self.create_cj_order(order.id)
                    if result.get('success'):
                        results['created'] += 1
                    else:
                        results['errors'] += 1
                    results['details'].append({
                        'order_number': order.order_number,
                        'action': 'create',
                        'result': result
                    })
                else:
                    # Synchroniser le statut
                    result = self.sync_order_status(order.id)
                    if result.get('success'):
                        results['synced'] += 1
                    else:
                        results['errors'] += 1
                    results['details'].append({
                        'order_number': order.order_number,
                        'action': 'sync',
                        'result': result
                    })
            
            return {
                'success': True,
                'message': f"{results['created']} créées, {results['synced']} synchronisées, {results['errors']} erreurs",
                'results': results
            }
            
        except Exception as e:
            logger.error(f"[CjOrderService] Exception sync_all_pending_orders: {e}")
            return {
                'success': False,
                'message': str(e)
            }
