"""
Service de configuration des webhooks CJ via leur API
Permet de configurer l'URL de webhook dans le dashboard CJ
"""
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class CjWebhookConfig:
    """Configuration des webhooks CJ via API"""
    
    def __init__(self, cj_api):
        """
        Initialiser le service de configuration
        
        Args:
            cj_api: Instance de CJDropshippingProvider
        """
        self.cj_api = cj_api
    
    def set_webhook_url(self, webhook_url: str) -> Dict:
        """
        Configurer l'URL de webhook dans CJ
        
        API: POST /api2.0/v1/webhook/setting
        
        Args:
            webhook_url: URL complète du webhook (ex: https://tonyalpha80.com/webhooks/cj/message)
            
        Returns:
            Dict avec le résultat
        """
        try:
            logger.info(f"🔧 Configuration webhook CJ: {webhook_url}")
            
            # Données pour l'API CJ
            data = {
                'url': webhook_url,
                'enable': True
            }
            
            # Appeler l'API CJ
            response = self.cj_api._make_request(
                'POST',
                '/webhook/setting',
                data=data
            )
            
            if response.get('code') == 200:
                logger.info(f"✅ Webhook CJ configuré avec succès")
                return {
                    'success': True,
                    'message': 'Webhook configuré',
                    'url': webhook_url
                }
            else:
                error_msg = response.get('message', 'Erreur inconnue')
                logger.error(f"❌ Erreur configuration webhook: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg
                }
                
        except Exception as e:
            logger.error(f"❌ Exception configuration webhook: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_webhook_config(self) -> Dict:
        """
        Récupérer la configuration actuelle du webhook
        
        Returns:
            Dict avec la configuration
        """
        try:
            logger.info("📋 Récupération configuration webhook CJ")
            
            # Appeler l'API CJ
            response = self.cj_api._make_request(
                'GET',
                '/webhook/setting'
            )
            
            if response.get('code') == 200:
                data = response.get('data', {})
                return {
                    'success': True,
                    'url': data.get('url'),
                    'enabled': data.get('enable', False)
                }
            else:
                error_msg = response.get('message', 'Erreur inconnue')
                return {
                    'success': False,
                    'error': error_msg
                }
                
        except Exception as e:
            logger.error(f"❌ Exception récupération config webhook: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def disable_webhook(self) -> Dict:
        """
        Désactiver le webhook CJ
        
        Returns:
            Dict avec le résultat
        """
        try:
            logger.info("🔕 Désactivation webhook CJ")
            
            data = {
                'enable': False
            }
            
            response = self.cj_api._make_request(
                'POST',
                '/webhook/setting',
                data=data
            )
            
            if response.get('code') == 200:
                logger.info("✅ Webhook CJ désactivé")
                return {
                    'success': True,
                    'message': 'Webhook désactivé'
                }
            else:
                error_msg = response.get('message', 'Erreur inconnue')
                return {
                    'success': False,
                    'error': error_msg
                }
                
        except Exception as e:
            logger.error(f"❌ Exception désactivation webhook: {e}")
            return {
                'success': False,
                'error': str(e)
            }
