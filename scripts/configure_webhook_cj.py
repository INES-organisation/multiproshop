"""
Script de configuration du webhook CJ Dropshipping
Configure l'URL du webhook via l'API CJ
"""
import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from models.api_provider import ApiProvider
from services.api_providers.cj_dropshipping_optimized import CJDropshippingProvider
from services.cj_webhook_config import CjWebhookConfig


def configure_webhook():
    """Configurer le webhook CJ via l'API"""
    
    with app.app_context():
        print("\n" + "="*70)
        print("🔧 CONFIGURATION WEBHOOK CJ DROPSHIPPING")
        print("="*70)
        
        # URL du webhook
        webhook_url = "https://tonyalpha80.com/webhooks/cj/message"
        
        print(f"\n📍 URL du webhook: {webhook_url}")
        print("\n⏳ Récupération du provider CJ...")
        
        # Récupérer le provider CJ
        provider = ApiProvider.query.filter_by(name='CJ Dropshipping').first()
        
        if not provider:
            print("❌ Provider CJ Dropshipping non trouvé dans la base de données")
            print("\nAssurez-vous que le provider CJ est configuré dans la base.")
            return False
        
        print(f"✅ Provider trouvé: {provider.name}")
        
        # Créer l'instance API
        print("\n⏳ Connexion à l'API CJ...")
        cj_api = CJDropshippingProvider(provider)
        
        # Créer le service de configuration
        webhook_config = CjWebhookConfig(cj_api)
        
        # Récupérer la configuration actuelle
        print("\n📋 Récupération de la configuration actuelle...")
        current_config = webhook_config.get_webhook_config()
        
        if current_config.get('success'):
            print(f"✅ Configuration actuelle:")
            print(f"   URL: {current_config.get('url', 'Non configurée')}")
            print(f"   Activé: {current_config.get('enabled', False)}")
        else:
            print(f"⚠️ Impossible de récupérer la config: {current_config.get('error')}")
        
        # Configurer le nouveau webhook
        print(f"\n⏳ Configuration du webhook: {webhook_url}")
        result = webhook_config.set_webhook_url(webhook_url)
        
        if result.get('success'):
            print("\n" + "="*70)
            print("✅ WEBHOOK CONFIGURÉ AVEC SUCCÈS !")
            print("="*70)
            print(f"\n📍 URL: {webhook_url}")
            print("\n✨ Le webhook est maintenant actif.")
            print("   CJ enverra les notifications à cette URL.")
            print("\n📝 Types de messages supportés:")
            print("   - ORDER: Mises à jour commandes")
            print("   - STOCK: Mises à jour stock")
            print("   - LOGISTIC: Mises à jour tracking")
            print("   - PRODUCT: Mises à jour produits")
            print("   - VARIANT: Mises à jour variantes")
            print("   - ORDERSPLIT: Divisions de commandes")
            return True
        else:
            print("\n" + "="*70)
            print("❌ ERREUR DE CONFIGURATION")
            print("="*70)
            print(f"\n⚠️ Erreur: {result.get('error')}")
            print("\n💡 Solutions possibles:")
            print("   1. Vérifier que les identifiants CJ sont corrects dans .env")
            print("   2. Vérifier que l'API CJ est accessible")
            print("   3. Configurer manuellement dans le dashboard CJ:")
            print("      https://cjdropshipping.com → Settings → Webhooks")
            return False


if __name__ == '__main__':
    try:
        success = configure_webhook()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
