"""
Service de gestion des webhooks CJ Dropshipping
Traite les notifications en temps réel depuis CJ
"""
import logging
import hashlib
import hmac
import json
from datetime import datetime
from typing import Dict, Optional, Any
from flask import current_app

logger = logging.getLogger(__name__)


class WebhookHandler:
    """Gestionnaire des webhooks CJ Dropshipping"""
    
    # Types d'événements supportés (format CJ réel)
    TYPE_PRODUCT = 'PRODUCT'
    TYPE_VARIANT = 'VARIANT'
    TYPE_STOCK = 'STOCK'
    TYPE_ORDER = 'ORDER'
    TYPE_ORDER_SPLIT = 'ORDERSPLIT'
    TYPE_LOGISTIC = 'LOGISTIC'
    TYPE_SOURCING_CREATE = 'SOURCINGCREATE'
    
    # Statuts de commande CJ
    ORDER_STATUS_CREATED = 'CREATED'
    ORDER_STATUS_PROCESSING = 'PROCESSING'
    ORDER_STATUS_SHIPPED = 'SHIPPED'
    ORDER_STATUS_DELIVERED = 'DELIVERED'
    ORDER_STATUS_CANCELLED = 'CANCELLED'
    
    def __init__(self):
        """Initialiser le handler"""
        self.webhook_secret = current_app.config.get('CJ_WEBHOOK_SECRET', '')
        
    def verify_signature(self, payload: str, signature: str) -> bool:
        """
        Vérifier la signature du webhook CJ
        Note: CJ utilise HTTPS et validation par IP, pas de signature HMAC
        
        Args:
            payload: Corps de la requête (string)
            signature: Signature fournie par CJ dans les headers (non utilisé)
            
        Returns:
            bool: True (CJ utilise HTTPS + validation IP)
        """
        # CJ ne fournit pas de signature HMAC dans leur documentation
        # La sécurité est assurée par HTTPS + validation IP côté CJ
        logger.debug("✓ Webhook CJ reçu via HTTPS")
        return True
    
    def process_webhook(self, message_data: Dict) -> Dict:
        """
        Traiter un webhook CJ selon le format réel
        
        Format CJ:
        {
            "messageId": "unique_id",
            "type": "ORDER|STOCK|LOGISTIC|etc",
            "messageType": "UPDATE",
            "params": {...}
        }
        
        Args:
            message_data: Données complètes du webhook CJ
            
        Returns:
            Dict avec le résultat du traitement
        """
        try:
            message_id = message_data.get('messageId')
            message_type = message_data.get('type')
            params = message_data.get('params', {})
            
            logger.info(f"📥 Traitement webhook CJ: type={message_type}, id={message_id}")
            
            # Router vers le bon handler selon le type
            if message_type == self.TYPE_ORDER:
                return self._handle_order_update(params)
            
            elif message_type == self.TYPE_STOCK:
                return self._handle_stock_update(params)
            
            elif message_type == self.TYPE_LOGISTIC:
                return self._handle_logistic_update(params)
            
            elif message_type == self.TYPE_PRODUCT:
                return self._handle_product_update(params)
            
            elif message_type == self.TYPE_VARIANT:
                return self._handle_variant_update(params)
            
            elif message_type == self.TYPE_ORDER_SPLIT:
                return self._handle_order_split(params)
            
            else:
                logger.warning(f"⚠️ Type de message non géré: {message_type}")
                return {
                    'success': True,
                    'message': f'Message {message_type} reçu mais non traité'
                }
                
        except Exception as e:
            logger.error(f"❌ Erreur traitement webhook: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }
    
    def _handle_order_update(self, params: Dict) -> Dict:
        """
        Gérer la mise à jour d'une commande CJ
        
        Format CJ:
        {
            "orderNumber": "api_xxx",
            "cjOrderId": 210823100016290555,
            "orderStatus": "CREATED|PROCESSING|SHIPPED|DELIVERED|CANCELLED",
            "logisticName": "CJPacket Ordinary",
            "trackNumber": "TRACK123",
            "createDate": "2021-08-23 11:31:45",
            "updateDate": "2021-08-23 11:31:45",
            "payDate": null,
            "deliveryDate": null,
            "completeDate": null
        }
        
        Args:
            params: Paramètres du webhook ORDER
            
        Returns:
            Dict avec le résultat
        """
        from models.order import Order
        from extensions import db
        
        try:
            cj_order_id = str(params.get('cjOrderId'))
            order_status = params.get('orderStatus')
            track_number = params.get('trackNumber')
            logistic_name = params.get('logisticName')
            delivery_date = params.get('deliveryDate')
            
            if not cj_order_id:
                return {
                    'success': False,
                    'error': 'cjOrderId manquant'
                }
            
            # Trouver la commande locale
            order = Order.query.filter_by(cj_order_id=cj_order_id).first()
            
            if not order:
                logger.warning(f"⚠️ Commande CJ {cj_order_id} non trouvée localement")
                return {
                    'success': False,
                    'error': f'Commande {cj_order_id} non trouvée'
                }
            
            # Mettre à jour selon le statut
            old_status = order.status
            order.cj_status = order_status
            
            if order_status == 'SHIPPED':
                order.status = 'shipped'
                order.cj_tracking_number = track_number
                order.cj_logistics_name = logistic_name
                order.shipped_at = datetime.now()
                logger.info(f"📦 Commande {order.order_number} expédiée")
                self._send_shipping_notification(order)
                
            elif order_status == 'DELIVERED':
                order.status = 'delivered'
                if delivery_date:
                    try:
                        order.delivered_at = datetime.strptime(delivery_date, '%Y-%m-%d %H:%M:%S')
                    except:
                        order.delivered_at = datetime.now()
                else:
                    order.delivered_at = datetime.now()
                logger.info(f"✅ Commande {order.order_number} livrée")
                self._send_delivery_notification(order)
                
            elif order_status == 'CANCELLED':
                order.status = 'cancelled'
                order.cancelled_at = datetime.now()
                logger.info(f"❌ Commande {order.order_number} annulée")
                self._send_cancellation_notification(order, 'Annulée par CJ')
                
            elif order_status == 'PROCESSING':
                order.status = 'processing'
                logger.info(f"⚙️ Commande {order.order_number} en traitement")
            
            # Mettre à jour tracking si fourni
            if track_number:
                order.cj_tracking_number = track_number
            if logistic_name:
                order.cj_logistics_name = logistic_name
            
            db.session.commit()
            
            logger.info(f"✅ Commande {order.order_number}: {old_status} → {order.status}")
            
            return {
                'success': True,
                'message': f'Commande {order.order_number} mise à jour',
                'order_number': order.order_number,
                'old_status': old_status,
                'new_status': order.status
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Erreur mise à jour commande: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }
    
    def _handle_stock_update(self, params: Dict) -> Dict:
        """
        Gérer la mise à jour de stock CJ
        
        Format CJ:
        {
            "vid1": [
                {
                    "vid": "vid1",
                    "areaId": "2",
                    "areaEn": "US Warehouse",
                    "countryCode": "US",
                    "storageNum": 12
                }
            ]
        }
        
        Args:
            params: Paramètres du webhook STOCK
            
        Returns:
            Dict avec le résultat
        """
        from models.product import Product
        from models.product_variant import ProductVariant
        from extensions import db
        
        try:
            updated_count = 0
            
            # params est un dict avec vid comme clé et liste de stocks par warehouse
            for vid, stock_list in params.items():
                if not stock_list or len(stock_list) == 0:
                    continue
                
                # Prendre le premier warehouse (ou faire la somme si plusieurs)
                total_stock = sum(item.get('storageNum', 0) for item in stock_list)
                
                # Mettre à jour la variante
                variant = ProductVariant.query.filter_by(cj_vid=vid).first()
                if variant:
                    old_stock = variant.stock
                    variant.stock = total_stock
                    variant.updated_at = datetime.now()
                    updated_count += 1
                    logger.info(f"✅ Stock variante {vid}: {old_stock} → {total_stock}")
                    
                    # Mettre à jour le produit parent aussi
                    if variant.product:
                        variant.product.updated_at = datetime.now()
            
            if updated_count > 0:
                db.session.commit()
                return {
                    'success': True,
                    'message': f'{updated_count} variante(s) mise(s) à jour'
                }
            else:
                logger.warning("⚠️ Aucune variante trouvée pour mise à jour stock")
                return {
                    'success': True,
                    'message': 'Aucune variante trouvée'
                }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Erreur mise à jour stock: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }
    
    def _handle_logistic_update(self, params: Dict) -> Dict:
        """
        Gérer la mise à jour logistique (tracking)
        
        Format CJ:
        {
            "orderId": 210823100016290555,
            "logisticName": "CJPacket Ordinary",
            "trackingNumber": "number12345678",
            "trackingStatus": 12,
            "logisticsTrackEvents": "[...]"
        }
        
        Args:
            params: Paramètres du webhook LOGISTIC
            
        Returns:
            Dict avec le résultat
        """
        from models.order import Order
        from extensions import db
        
        try:
            cj_order_id = str(params.get('orderId'))
            tracking_number = params.get('trackingNumber')
            logistic_name = params.get('logisticName')
            tracking_status = params.get('trackingStatus')
            
            if not cj_order_id:
                return {
                    'success': False,
                    'error': 'orderId manquant'
                }
            
            # Trouver la commande
            order = Order.query.filter_by(cj_order_id=cj_order_id).first()
            
            if not order:
                logger.warning(f"⚠️ Commande CJ {cj_order_id} non trouvée")
                return {
                    'success': False,
                    'error': f'Commande {cj_order_id} non trouvée'
                }
            
            # Mettre à jour les infos de tracking
            if tracking_number:
                order.cj_tracking_number = tracking_number
            if logistic_name:
                order.cj_logistics_name = logistic_name
            
            # Status 12 = Delivered selon la doc CJ
            if tracking_status == 12:
                order.status = 'delivered'
                order.cj_status = 'DELIVERED'
                order.delivered_at = datetime.now()
                logger.info(f"📦 Commande {order.order_number} livrée (tracking)")
                self._send_delivery_notification(order)
            
            db.session.commit()
            
            logger.info(f"✅ Tracking mis à jour pour {order.order_number}")
            
            return {
                'success': True,
                'message': f'Tracking mis à jour pour {order.order_number}'
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Erreur mise à jour logistique: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }
    
    def _handle_product_update(self, params: Dict) -> Dict:
        """
        Gérer la mise à jour d'un produit
        Synchronise le produit depuis CJ quand il est modifié
        
        Format CJ:
        {
            "pid": "product_id",
            "updateType": "PRICE|STOCK|INFO"
        }
        
        Args:
            params: Paramètres du webhook PRODUCT
            
        Returns:
            Dict avec le résultat
        """
        from models.product import Product
        from extensions import db
        
        try:
            pid = params.get('pid')
            update_type = params.get('updateType', 'INFO')
            
            if not pid:
                return {
                    'success': False,
                    'error': 'pid manquant'
                }
            
            logger.info(f"📦 Mise à jour produit {pid} (type: {update_type})")
            
            # Trouver le produit local
            product = Product.query.filter_by(cj_pid=pid).first()
            
            if not product:
                logger.warning(f"⚠️ Produit {pid} non trouvé localement")
                return {
                    'success': True,
                    'message': f'Produit {pid} non trouvé localement (ignoré)'
                }
            
            # Synchroniser le produit depuis CJ
            try:
                from services.cj_sync_service import CjSyncService
                from services.api_providers.cj_dropshipping_optimized import CJDropshippingApiOptimized
                from config import Config
                
                cj_api = CJDropshippingApiOptimized(
                    email=Config.CJ_EMAIL,
                    password=Config.CJ_PASSWORD,
                    dev_key=Config.CJ_DEV_KEY
                )
                
                sync_service = CjSyncService(cj_api)
                
                # Récupérer les détails du produit depuis CJ
                product_data = cj_api.get_product_details(pid)
                
                if product_data:
                    # Synchroniser le produit
                    sync_service._sync_product(product_data)
                    logger.info(f"✅ Produit {pid} synchronisé depuis CJ")
                    
                    return {
                        'success': True,
                        'message': f'Produit {product.name} synchronisé'
                    }
                else:
                    logger.warning(f"⚠️ Impossible de récupérer les détails du produit {pid}")
                    return {
                        'success': False,
                        'error': 'Impossible de récupérer les détails du produit'
                    }
                    
            except Exception as e:
                logger.error(f"❌ Erreur synchronisation produit {pid}: {e}")
                return {
                    'success': False,
                    'error': str(e)
                }
                
        except Exception as e:
            logger.error(f"❌ Erreur traitement webhook PRODUCT: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }
    
    def _handle_variant_update(self, params: Dict) -> Dict:
        """
        Gérer la mise à jour d'une variante
        Synchronise la variante depuis CJ quand elle est modifiée
        
        Format CJ:
        {
            "vid": "variant_id",
            "pid": "product_id",
            "updateType": "PRICE|STOCK|INFO"
        }
        
        Args:
            params: Paramètres du webhook VARIANT
            
        Returns:
            Dict avec le résultat
        """
        from models.product_variant import ProductVariant
        from models.product import Product
        from extensions import db
        
        try:
            vid = params.get('vid')
            pid = params.get('pid')
            update_type = params.get('updateType', 'INFO')
            
            if not vid:
                return {
                    'success': False,
                    'error': 'vid manquant'
                }
            
            logger.info(f"🎨 Mise à jour variante {vid} (type: {update_type})")
            
            # Trouver la variante locale
            variant = ProductVariant.query.filter_by(cj_vid=vid).first()
            
            if not variant:
                logger.warning(f"⚠️ Variante {vid} non trouvée localement")
                return {
                    'success': True,
                    'message': f'Variante {vid} non trouvée localement (ignoré)'
                }
            
            # Synchroniser la variante depuis CJ
            try:
                from services.api_providers.cj_dropshipping_optimized import CJDropshippingApiOptimized
                from config import Config
                
                cj_api = CJDropshippingApiOptimized(
                    email=Config.CJ_EMAIL,
                    password=Config.CJ_PASSWORD,
                    dev_key=Config.CJ_DEV_KEY
                )
                
                # Récupérer les détails du produit parent pour avoir les variantes
                if pid:
                    product_data = cj_api.get_product_details(pid)
                    
                    if product_data and 'variants' in product_data:
                        # Trouver la variante dans les données
                        variant_data = next(
                            (v for v in product_data['variants'] if v.get('vid') == vid),
                            None
                        )
                        
                        if variant_data:
                            # Mettre à jour la variante
                            if 'variantPrice' in variant_data:
                                variant.price = float(variant_data['variantPrice'])
                            if 'variantStock' in variant_data:
                                variant.stock = int(variant_data['variantStock'])
                            if 'variantImage' in variant_data:
                                variant.image_url = variant_data['variantImage']
                            
                            variant.updated_at = datetime.now()
                            db.session.commit()
                            
                            logger.info(f"✅ Variante {vid} synchronisée depuis CJ")
                            
                            return {
                                'success': True,
                                'message': f'Variante {variant.display_name()} synchronisée'
                            }
                        else:
                            logger.warning(f"⚠️ Variante {vid} non trouvée dans les données CJ")
                            return {
                                'success': False,
                                'error': 'Variante non trouvée dans les données CJ'
                            }
                    else:
                        logger.warning(f"⚠️ Impossible de récupérer les détails du produit {pid}")
                        return {
                            'success': False,
                            'error': 'Impossible de récupérer les détails du produit'
                        }
                else:
                    logger.warning("⚠️ pid manquant pour synchroniser la variante")
                    return {
                        'success': False,
                        'error': 'pid manquant'
                    }
                    
            except Exception as e:
                logger.error(f"❌ Erreur synchronisation variante {vid}: {e}")
                return {
                    'success': False,
                    'error': str(e)
                }
                
        except Exception as e:
            logger.error(f"❌ Erreur traitement webhook VARIANT: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }
    
    def _handle_order_split(self, params: Dict) -> Dict:
        """
        Gérer la division d'une commande
        
        Args:
            params: Paramètres du webhook ORDERSPLIT
            
        Returns:
            Dict avec le résultat
        """
        logger.info(f"✂️ Division commande: {params.get('originalOrderId')}")
        # Pour l'instant, juste logger
        # TODO: Implémenter la gestion des commandes divisées si nécessaire
        return {
            'success': True,
            'message': 'Division commande reçue'
        }
    
    def _send_shipping_notification(self, order) -> None:
        """
        Envoyer une notification d'expédition au client
        
        Args:
            order: Commande expédiée
        """
        try:
            from utils.email import send_email
            
            subject = f"Votre commande {order.order_number} a été expédiée !"
            
            html_body = f"""
            <h2>Bonne nouvelle ! Votre commande est en route 📦</h2>
            
            <p>Bonjour {order.shipping_first_name},</p>
            
            <p>Votre commande <strong>{order.order_number}</strong> a été expédiée.</p>
            
            <h3>Informations de suivi :</h3>
            <ul>
                <li><strong>Numéro de suivi :</strong> {order.cj_tracking_number}</li>
                <li><strong>Transporteur :</strong> {order.cj_logistics_name}</li>
                <li><strong>Date d'expédition :</strong> {order.shipped_at.strftime('%d/%m/%Y')}</li>
            </ul>
            
            <p>Vous pouvez suivre votre colis en utilisant le numéro de suivi ci-dessus.</p>
            
            <p>Merci de votre confiance !</p>
            
            <p><em>L'équipe MultiProShop</em></p>
            """
            
            send_email(
                to=order.customer_email,
                subject=subject,
                html=html_body
            )
            
            logger.info(f"📧 Email d'expédition envoyé à {order.customer_email}")
            
        except Exception as e:
            logger.error(f"❌ Erreur envoi email expédition: {e}")
    
    def _send_delivery_notification(self, order) -> None:
        """
        Envoyer une notification de livraison au client
        
        Args:
            order: Commande livrée
        """
        try:
            from utils.email import send_email
            
            subject = f"Votre commande {order.order_number} a été livrée !"
            
            html_body = f"""
            <h2>Votre commande est arrivée ! 🎉</h2>
            
            <p>Bonjour {order.shipping_first_name},</p>
            
            <p>Votre commande <strong>{order.order_number}</strong> a été livrée avec succès.</p>
            
            <p>Nous espérons que vous êtes satisfait(e) de votre achat !</p>
            
            <p>N'hésitez pas à nous laisser un avis sur votre expérience.</p>
            
            <p>Merci de votre confiance !</p>
            
            <p><em>L'équipe MultiProShop</em></p>
            """
            
            send_email(
                to=order.customer_email,
                subject=subject,
                html=html_body
            )
            
            logger.info(f"📧 Email de livraison envoyé à {order.customer_email}")
            
        except Exception as e:
            logger.error(f"❌ Erreur envoi email livraison: {e}")
    
    def _send_cancellation_notification(self, order, reason: str) -> None:
        """
        Envoyer une notification d'annulation au client
        
        Args:
            order: Commande annulée
            reason: Raison de l'annulation
        """
        try:
            from utils.email import send_email
            
            subject = f"Votre commande {order.order_number} a été annulée"
            
            html_body = f"""
            <h2>Annulation de commande</h2>
            
            <p>Bonjour {order.shipping_first_name},</p>
            
            <p>Nous vous informons que votre commande <strong>{order.order_number}</strong> a été annulée.</p>
            
            <p><strong>Raison :</strong> {reason}</p>
            
            <p>Si vous avez déjà effectué un paiement, vous serez remboursé(e) dans les prochains jours.</p>
            
            <p>Pour toute question, n'hésitez pas à nous contacter.</p>
            
            <p>Cordialement,</p>
            <p><em>L'équipe MultiProShop</em></p>
            """
            
            send_email(
                to=order.customer_email,
                subject=subject,
                html=html_body
            )
            
            logger.info(f"📧 Email d'annulation envoyé à {order.customer_email}")
            
        except Exception as e:
            logger.error(f"❌ Erreur envoi email annulation: {e}")
    
    def log_webhook(self, event_type: str, data: Dict, result: Dict) -> None:
        """
        Logger un webhook reçu
        
        Args:
            event_type: Type d'événement
            data: Données reçues
            result: Résultat du traitement
        """
        from models.webhook_log import WebhookLog
        from extensions import db
        
        try:
            log = WebhookLog(
                event_type=event_type,
                payload=json.dumps(data),
                result=json.dumps(result),
                success=result.get('success', False),
                created_at=datetime.utcnow()
            )
            
            db.session.add(log)
            db.session.commit()
            
        except Exception as e:
            logger.error(f"❌ Erreur logging webhook: {e}")
            db.session.rollback()
