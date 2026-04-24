"""
Script pour configurer le provider CJ Dropshipping
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from extensions import db
from models.api_provider import ApiProvider

def configure_cj_dropshipping():
    """Configurer CJ Dropshipping avec les identifiants"""
    with app.app_context():
        # Vérifier si le provider existe déjà
        provider = ApiProvider.query.filter_by(slug='cj-dropshipping').first()
        
        if provider:
            print(f"Provider CJ Dropshipping trouvé (ID: {provider.id})")
            print("Mise à jour des identifiants...")
            
            # Mettre à jour les identifiants
            provider.api_key = 'tonyalpha80@gmail.com'
            provider.api_secret = 'd0b2a7aa79024a149fd37128ccef9603'
            provider.api_endpoint = 'https://developers.cjdropshipping.com/api2.0/v1'
            provider.api_version = 'v1'
            provider.auth_type = 'signature'
            provider.is_active = True
            
        else:
            print("Création du provider CJ Dropshipping...")
            
            # Créer le provider
            provider = ApiProvider(
                name='CJ Dropshipping',
                slug='cj-dropshipping',
                description='Plateforme de dropshipping avec des millions de produits',
                provider_type='dropshipping',
                api_endpoint='https://developers.cjdropshipping.com/api2.0/v1',
                api_version='v1',
                auth_type='signature',
                api_key='tonyalpha80@gmail.com',
                api_secret='d0b2a7aa79024a149fd37128ccef9603',
                is_active=True,
                is_connected=False
            )
            
            db.session.add(provider)
        
        db.session.commit()
        
        print(f"\n✓ Provider configuré avec succès!")
        print(f"  - Nom: {provider.name}")
        print(f"  - Email: {provider.api_key}")
        print(f"  - API Key: {provider.api_secret[:10]}...")
        print(f"  - Endpoint: {provider.api_endpoint}")
        print(f"\nVous pouvez maintenant tester la connexion depuis l'interface admin.")
        
        return provider

if __name__ == '__main__':
    configure_cj_dropshipping()
