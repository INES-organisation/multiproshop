"""
Service de notifications admin pour erreurs critiques CJ Dropshipping
Envoie des emails aux administrateurs en cas de problèmes critiques
"""
import logging
from typing import List, Optional
from datetime import datetime, timedelta
from flask import current_app
from config import Config

logger = logging.getLogger(__name__)

# Cache pour éviter spam d'emails (même erreur dans les 30 minutes)
_notification_cache = {}
_CACHE_DURATION = 1800  # 30 minutes en secondes


class AdminNotificationService:
    """Service de notifications admin pour erreurs critiques"""
    
    @staticmethod
    def _should_notify(error_key: str) -> bool:
        """
        Vérifier si on doit envoyer une notification (éviter spam)
        
        Args:
            error_key: Clé unique de l'erreur
            
        Returns:
            True si on doit notifier, False sinon
        """
        import time
        
        current_time = time.time()
        
        if error_key in _notification_cache:
            last_notification = _notification_cache[error_key]
            if current_time - last_notification < _CACHE_DURATION:
                return False
        
        _notification_cache[error_key] = current_time
        return True
    
    @staticmethod
    def _get_admin_emails() -> List[str]:
        """
        Récupérer les emails des administrateurs
        
        Returns:
            Liste des emails admin
        """
        try:
            from models.user import User
            
            admins = User.query.filter_by(is_admin=True).all()
            return [admin.email for admin in admins if admin.email]
        except Exception as e:
            logger.error(f"Erreur récupération emails admin: {e}")
            # Fallback sur email de config
            if hasattr(Config, 'ADMIN_EMAIL') and Config.ADMIN_EMAIL:
                return [Config.ADMIN_EMAIL]
            return []
    
    @staticmethod
    def notify_cj_sync_failure(error_type: str, error_message: str, details: dict = None):
        """
        Notifier échec synchronisation CJ
        
        Args:
            error_type: Type d'erreur (PRODUCTS, STOCK, ORDERS, CATEGORIES)
            error_message: Message d'erreur
            details: Détails additionnels
        """
        error_key = f"cj_sync_{error_type}"
        
        if not AdminNotificationService._should_notify(error_key):
            logger.info(f"Notification {error_key} déjà envoyée récemment, ignorée")
            return
        
        try:
            from utils.email import send_email
            
            admin_emails = AdminNotificationService._get_admin_emails()
            
            if not admin_emails:
                logger.warning("Aucun email admin configuré pour notifications")
                return
            
            subject = f"⚠️ Échec synchronisation CJ - {error_type}"
            
            details_html = ""
            if details:
                details_html = "<h3>Détails:</h3><ul>"
                for key, value in details.items():
                    details_html += f"<li><strong>{key}:</strong> {value}</li>"
                details_html += "</ul>"
            
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <div style="background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin-bottom: 20px;">
                    <h2 style="color: #856404; margin-top: 0;">⚠️ Échec Synchronisation CJ Dropshipping</h2>
                </div>
                
                <p><strong>Type:</strong> {error_type}</p>
                <p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                
                <h3>Message d'erreur:</h3>
                <div style="background-color: #f8f9fa; padding: 10px; border-radius: 4px; font-family: monospace;">
                    {error_message}
                </div>
                
                {details_html}
                
                <hr style="margin: 30px 0;">
                
                <h3>Actions recommandées:</h3>
                <ul>
                    <li>Vérifier les logs de synchronisation</li>
                    <li>Vérifier la connexion à l'API CJ</li>
                    <li>Vérifier les credentials CJ dans .env</li>
                    <li>Relancer la synchronisation manuellement si nécessaire</li>
                </ul>
                
                <p style="color: #6c757d; font-size: 12px; margin-top: 30px;">
                    Cette notification ne sera pas renvoyée pour la même erreur pendant 30 minutes.
                </p>
            </body>
            </html>
            """
            
            for admin_email in admin_emails:
                send_email(
                    to=admin_email,
                    subject=subject,
                    html=html_body
                )
            
            logger.info(f"Notification envoyée à {len(admin_emails)} admin(s) pour {error_type}")
            
        except Exception as e:
            logger.error(f"Erreur envoi notification admin: {e}")
    
    @staticmethod
    def notify_cj_api_down(error_message: str):
        """
        Notifier que l'API CJ est inaccessible
        
        Args:
            error_message: Message d'erreur
        """
        error_key = "cj_api_down"
        
        if not AdminNotificationService._should_notify(error_key):
            return
        
        try:
            from utils.email import send_email
            
            admin_emails = AdminNotificationService._get_admin_emails()
            
            if not admin_emails:
                return
            
            subject = "🔴 API CJ Dropshipping inaccessible"
            
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <div style="background-color: #f8d7da; border-left: 4px solid #dc3545; padding: 15px; margin-bottom: 20px;">
                    <h2 style="color: #721c24; margin-top: 0;">🔴 API CJ Dropshipping Inaccessible</h2>
                </div>
                
                <p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                
                <h3>Message d'erreur:</h3>
                <div style="background-color: #f8f9fa; padding: 10px; border-radius: 4px; font-family: monospace;">
                    {error_message}
                </div>
                
                <hr style="margin: 30px 0;">
                
                <h3>Impact:</h3>
                <ul>
                    <li>❌ Synchronisation produits impossible</li>
                    <li>❌ Synchronisation stock impossible</li>
                    <li>❌ Création commandes CJ impossible</li>
                    <li>❌ Webhooks peuvent ne pas fonctionner</li>
                </ul>
                
                <h3>Actions recommandées:</h3>
                <ul>
                    <li>Vérifier le statut de l'API CJ: <a href="https://developers.cjdropshipping.com">https://developers.cjdropshipping.com</a></li>
                    <li>Vérifier les credentials dans .env</li>
                    <li>Vérifier la connexion internet du serveur</li>
                    <li>Contacter le support CJ si le problème persiste</li>
                </ul>
                
                <p style="color: #6c757d; font-size: 12px; margin-top: 30px;">
                    Cette notification ne sera pas renvoyée pendant 30 minutes.
                </p>
            </body>
            </html>
            """
            
            for admin_email in admin_emails:
                send_email(
                    to=admin_email,
                    subject=subject,
                    html=html_body
                )
            
            logger.info(f"Notification API down envoyée à {len(admin_emails)} admin(s)")
            
        except Exception as e:
            logger.error(f"Erreur envoi notification API down: {e}")
    
    @staticmethod
    def notify_webhook_failure(webhook_type: str, error_message: str, webhook_data: dict = None):
        """
        Notifier échec traitement webhook
        
        Args:
            webhook_type: Type de webhook (ORDER, STOCK, PRODUCT, etc.)
            error_message: Message d'erreur
            webhook_data: Données du webhook
        """
        error_key = f"webhook_{webhook_type}"
        
        if not AdminNotificationService._should_notify(error_key):
            return
        
        try:
            from utils.email import send_email
            
            admin_emails = AdminNotificationService._get_admin_emails()
            
            if not admin_emails:
                return
            
            subject = f"⚠️ Échec traitement webhook CJ - {webhook_type}"
            
            webhook_html = ""
            if webhook_data:
                import json
                webhook_html = f"""
                <h3>Données webhook:</h3>
                <div style="background-color: #f8f9fa; padding: 10px; border-radius: 4px; font-family: monospace; font-size: 12px; overflow-x: auto;">
                    <pre>{json.dumps(webhook_data, indent=2)}</pre>
                </div>
                """
            
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <div style="background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin-bottom: 20px;">
                    <h2 style="color: #856404; margin-top: 0;">⚠️ Échec Traitement Webhook CJ</h2>
                </div>
                
                <p><strong>Type:</strong> {webhook_type}</p>
                <p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                
                <h3>Message d'erreur:</h3>
                <div style="background-color: #f8f9fa; padding: 10px; border-radius: 4px; font-family: monospace;">
                    {error_message}
                </div>
                
                {webhook_html}
                
                <hr style="margin: 30px 0;">
                
                <h3>Actions recommandées:</h3>
                <ul>
                    <li>Vérifier les logs webhook: /admin/webhooks/cj/logs</li>
                    <li>Vérifier que les données du webhook sont valides</li>
                    <li>Vérifier que les produits/commandes existent localement</li>
                    <li>Le webhook sera peut-être renvoyé par CJ automatiquement</li>
                </ul>
                
                <p style="color: #6c757d; font-size: 12px; margin-top: 30px;">
                    Cette notification ne sera pas renvoyée pour le même type pendant 30 minutes.
                </p>
            </body>
            </html>
            """
            
            for admin_email in admin_emails:
                send_email(
                    to=admin_email,
                    subject=subject,
                    html=html_body
                )
            
            logger.info(f"Notification webhook failure envoyée à {len(admin_emails)} admin(s)")
            
        except Exception as e:
            logger.error(f"Erreur envoi notification webhook: {e}")
    
    @staticmethod
    def notify_stock_critical(product_name: str, product_id: int, current_stock: int):
        """
        Notifier stock critique d'un produit
        
        Args:
            product_name: Nom du produit
            product_id: ID du produit
            current_stock: Stock actuel
        """
        error_key = f"stock_critical_{product_id}"
        
        if not AdminNotificationService._should_notify(error_key):
            return
        
        try:
            from utils.email import send_email
            
            admin_emails = AdminNotificationService._get_admin_emails()
            
            if not admin_emails:
                return
            
            subject = f"📦 Stock critique - {product_name}"
            
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <div style="background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin-bottom: 20px;">
                    <h2 style="color: #856404; margin-top: 0;">📦 Stock Critique Détecté</h2>
                </div>
                
                <p><strong>Produit:</strong> {product_name}</p>
                <p><strong>ID:</strong> {product_id}</p>
                <p><strong>Stock actuel:</strong> <span style="color: #dc3545; font-weight: bold;">{current_stock} unités</span></p>
                <p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                
                <hr style="margin: 30px 0;">
                
                <h3>Actions recommandées:</h3>
                <ul>
                    <li>Vérifier le stock sur CJ Dropshipping</li>
                    <li>Désactiver le produit si rupture de stock</li>
                    <li>Contacter CJ pour réapprovisionnement</li>
                    <li>Informer les clients si commandes en attente</li>
                </ul>
                
                <p style="color: #6c757d; font-size: 12px; margin-top: 30px;">
                    Cette notification ne sera pas renvoyée pour ce produit pendant 30 minutes.
                </p>
            </body>
            </html>
            """
            
            for admin_email in admin_emails:
                send_email(
                    to=admin_email,
                    subject=subject,
                    html=html_body
                )
            
            logger.info(f"Notification stock critique envoyée pour produit {product_id}")
            
        except Exception as e:
            logger.error(f"Erreur envoi notification stock critique: {e}")
