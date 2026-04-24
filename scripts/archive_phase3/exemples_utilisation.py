from app import create_app, db
from models.supplier import Supplier
from models.marketplace import Marketplace
from models.video import Video
from models.ai_recommendation import AIRecommendation
from models.api_integration import ApiIntegration
from models.product import Product
from models.user import User

# Exemples d'utilisation des nouveaux modèles
def exemples():
    app = create_app()
    with app.app_context():
        # 1. Ajouter un fournisseur (dropshipping)
        supplier = Supplier(name='SuperDropship', contact_email='contact@superdropship.com', website='https://superdropship.com')
        db.session.add(supplier)
        db.session.commit()
        print('Fournisseur ajouté:', supplier)

        # 2. Ajouter une marketplace
        market = Marketplace(name='MegaMarket', description='Marketplace internationale', url='https://megamarket.com')
        db.session.add(market)
        db.session.commit()
        print('Marketplace ajoutée:', market)

        # 3. Ajouter une vidéo à un produit existant (id=1)
        video = Video(url='https://youtu.be/demo', title='Présentation produit', description='Vidéo démo', product_id=1)
        db.session.add(video)
        db.session.commit()
        print('Vidéo ajoutée:', video)

        # 4. Ajouter une recommandation IA
        reco = AIRecommendation(user_id=1, product_id=1, score=0.98, reason='Basé sur l’historique et préférences')
        db.session.add(reco)
        db.session.commit()
        print('Reco IA ajoutée:', reco)

        # 5. Ajouter une intégration API
        api = ApiIntegration(name='API Dropshipping', api_url='https://api.dropship.com', api_key='demo-key')
        db.session.add(api)
        db.session.commit()
        print('API intégrée:', api)

if __name__ == '__main__':
    exemples()
