import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from models.api_provider import ApiProvider

def check_cj_credentials():
    """Vérifier les credentials CJ"""
    with app.app_context():
        provider = ApiProvider.query.filter_by(slug='cj-dropshipping').first()
        
        if not provider:
            print("❌ Provider CJ Dropshipping non trouvé")
            return
        
        print("\n" + "="*60)
        print("CREDENTIALS CJ DROPSHIPPING")
        print("="*60)
        print(f"ID: {provider.id}")
        print(f"Nom: {provider.name}")
        print(f"Slug: {provider.slug}")
        print(f"API Key: {provider.api_key[:20]}..." if provider.api_key else "Non défini")
        print(f"API Secret: {provider.api_secret[:20]}..." if provider.api_secret else "Non défini")
        print(f"Endpoint: {provider.api_endpoint}")
        print(f"Actif: {provider.is_active}")
        print("="*60)
        
        if not provider.api_key or not provider.api_secret:
            print("\n⚠️  Les credentials CJ ne sont pas configurés")
            print("💡 Vous devez configurer l'API key et l'API secret dans l'admin")
        else:
            print("\n✅ Credentials configurés")
            print("\n💡 Si l'API ne fonctionne pas, vérifiez que:")
            print("   1. L'API key et secret sont corrects")
            print("   2. Votre compte CJ est actif")
            print("   3. Vous n'avez pas atteint la limite de requêtes")

if __name__ == '__main__':
    check_cj_credentials()
