"""
Script de configuration automatique des webhooks CJ Dropshipping
Configure l'URL du webhook sur le dashboard CJ via l'API
"""
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from services.api_providers.cj_dropshipping_optimized import CJDropshippingApiOptimized
from services.cj_webhook_config import CjWebhookConfig
from config import Config
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_webhooks():
    """Configurer les webhooks CJ automatiquement"""
    
    with app.app_context():
        logger.info("="*70)
        logger.info("🔧 CONFIGURATION WEBHOOKS CJ DROPSHIPPING")
        logger.info("="*70)
        logger.info(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # URL du webhook (depuis .env ou config)
        webhook_url = Config.CJ_WEBHOOK_URL
        
        if not webhook_url:
            logger.error("❌ CJ_WEBHOOK_URL non configurée dans .env")
            logger.info("\nAjouter dans .env:")
            logger.info("CJ_WEBHOOK_URL=https://votre-domaine.com/webhooks/cj/message")
            return False
        
        logger.info(f"\n📍 URL webhook: {webhook_url}")
        
        # Initialiser l'API CJ
        try:
            logger.info("\n🔑 Connexion à l'API CJ...")
            cj_api = CJDropshippingApiOptimized(
                email=Config.CJ_EMAIL,
                password=Config.CJ_PASSWORD,
                dev_key=Config.CJ_DEV_KEY
            )
            
            # Obtenir un token
            token = cj_api.get_access_token()
            if not token:
                logger.error("❌ Impossible d'obtenir un token CJ")
                return False
            
            logger.info("✅ Token CJ obtenu")
            
        except Exception as e:
            logger.error(f"❌ Erreur connexion API: {e}")
            return False
        
        # Configurer le webhook
        try:
            logger.info("\n🔧 Configuration du webhook...")
            webhook_config = CjWebhookConfig(cj_api)
            
            # Vérifier la configuration actuelle
            logger.info("📋 Vérification configuration actuelle...")
            current_config = webhook_config.get_webhook_config()
            
            if current_config.get('success'):
                current_url = current_config.get('url')
                current_enabled = current_config.get('enabled')
                
                logger.info(f"  URL actuelle: {current_url or 'Non configurée'}")
                logger.info(f"  Statut: {'Activé' if current_enabled else 'Désactivé'}")
                
                if current_url == webhook_url and current_enabled:
                    logger.info("\n✅ Webhook déjà configuré correctement")
                    return True
            
            # Configurer la nouvelle URL
            logger.info(f"\n🔄 Configuration de l'URL: {webhook_url}")
            result = webhook_config.set_webhook_url(webhook_url)
            
            if result.get('success'):
                logger.info("\n✅ Webhook configuré avec succès!")
                logger.info("\n" + "="*70)
                logger.info("📊 RÉSUMÉ")
                logger.info("="*70)
                logger.info(f"URL webhook: {webhook_url}")
                logger.info("Statut: Activé ✅")
                logger.info("\nTypes de webhooks supportés:")
                logger.info("  ✅ ORDER - Mises à jour commandes")
                logger.info("  ✅ STOCK - Mises à jour stock")
                logger.info("  ✅ LOGISTIC - Mises à jour tracking")
                logger.info("  ✅ PRODUCT - Mises à jour produits")
                logger.info("  ✅ VARIANT - Mises à jour variantes")
                logger.info("  ✅ ORDERSPLIT - Division commandes")
                logger.info("="*70)
                return True
            else:
                error = result.get('error', 'Erreur inconnue')
                logger.error(f"\n❌ Erreur configuration: {error}")
                return False
                
        except Exception as e:
            logger.error(f"\n❌ Exception configuration webhook: {e}")
            import traceback
            traceback.print_exc()
            return False


def test_webhook_endpoint():
    """Tester que l'endpoint webhook est accessible"""
    
    logger.info("\n🧪 TEST ENDPOINT WEBHOOK")
    logger.info("="*70)
    
    webhook_url = Config.CJ_WEBHOOK_URL
    
    if not webhook_url:
        logger.warning("⚠️ CJ_WEBHOOK_URL non configurée, test ignoré")
        return True
    
    try:
        import requests
        
        # Test simple GET (l'endpoint devrait répondre)
        logger.info(f"Test GET: {webhook_url}")
        response = requests.get(webhook_url, timeout=5)
        
        if response.status_code in [200, 404, 405]:
            logger.info(f"✅ Endpoint accessible (code: {response.status_code})")
            return True
        else:
            logger.warning(f"⚠️ Code inattendu: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        logger.error("❌ Impossible de se connecter à l'URL webhook")
        logger.info("Vérifier que:")
        logger.info("  1. Le serveur est démarré")
        logger.info("  2. L'URL est correcte")
        logger.info("  3. Le domaine est accessible depuis internet")
        return False
    except Exception as e:
        logger.error(f"❌ Erreur test endpoint: {e}")
        return False


def disable_webhooks():
    """Désactiver les webhooks CJ"""
    
    with app.app_context():
        logger.info("="*70)
        logger.info("🔕 DÉSACTIVATION WEBHOOKS CJ")
        logger.info("="*70)
        
        try:
            cj_api = CJDropshippingApiOptimized(
                email=Config.CJ_EMAIL,
                password=Config.CJ_PASSWORD,
                dev_key=Config.CJ_DEV_KEY
            )
            
            webhook_config = CjWebhookConfig(cj_api)
            result = webhook_config.disable_webhook()
            
            if result.get('success'):
                logger.info("✅ Webhooks désactivés")
                return True
            else:
                logger.error(f"❌ Erreur: {result.get('error')}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Exception: {e}")
            return False


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Configuration webhooks CJ Dropshipping')
    parser.add_argument('action', choices=['setup', 'test', 'disable', 'status'], 
                       help='Action à effectuer')
    
    args = parser.parse_args()
    
    try:
        if args.action == 'setup':
            success = setup_webhooks()
            sys.exit(0 if success else 1)
            
        elif args.action == 'test':
            success = test_webhook_endpoint()
            sys.exit(0 if success else 1)
            
        elif args.action == 'disable':
            success = disable_webhooks()
            sys.exit(0 if success else 1)
            
        elif args.action == 'status':
            with app.app_context():
                cj_api = CJDropshippingApiOptimized(
                    email=Config.CJ_EMAIL,
                    password=Config.CJ_PASSWORD,
                    dev_key=Config.CJ_DEV_KEY
                )
                webhook_config = CjWebhookConfig(cj_api)
                result = webhook_config.get_webhook_config()
                
                if result.get('success'):
                    logger.info("="*70)
                    logger.info("📊 STATUT WEBHOOKS CJ")
                    logger.info("="*70)
                    logger.info(f"URL: {result.get('url') or 'Non configurée'}")
                    logger.info(f"Statut: {'Activé ✅' if result.get('enabled') else 'Désactivé ❌'}")
                    logger.info("="*70)
                    sys.exit(0)
                else:
                    logger.error(f"❌ Erreur: {result.get('error')}")
                    sys.exit(1)
                    
    except Exception as e:
        logger.error(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
