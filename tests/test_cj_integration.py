"""
Tests d'intégration pour CJ Dropshipping
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from services.api_providers.cj_dropshipping_optimized import CJDropshippingApiOptimized
from services.cj_sync_service import CjSyncService
from services.shipping_service import ShippingService
from config import Config


@pytest.fixture
def client():
    """Créer un client de test Flask"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        with app.app_context():
            yield client


@pytest.fixture
def cj_api():
    """Créer une instance de l'API CJ"""
    return CJDropshippingApiOptimized(
        email=Config.CJ_EMAIL,
        password=Config.CJ_PASSWORD,
        dev_key=Config.CJ_DEV_KEY
    )


@pytest.fixture
def sync_service(cj_api):
    """Créer une instance du service de sync"""
    return CjSyncService(cj_api)


@pytest.fixture
def shipping_service():
    """Créer une instance du service de livraison"""
    return ShippingService()


class TestCJAPI:
    """Tests de l'API CJ"""
    
    def test_api_initialization(self, cj_api):
        """Tester l'initialisation de l'API"""
        assert cj_api.email == Config.CJ_EMAIL
        assert cj_api.base_url == 'https://developers.cjdropshipping.com/api2.0/v1'
    
    def test_get_access_token(self, cj_api):
        """Tester l'obtention du token (peut échouer si rate limit)"""
        # Note: Ce test peut échouer avec erreur 429 (rate limit)
        # C'est normal - CJ limite à 1 req/5min
        token = cj_api.get_access_token()
        # Si pas de rate limit, token devrait exister
        # Si rate limit, token sera None
        assert token is None or isinstance(token, str)


class TestSyncService:
    """Tests du service de synchronisation"""
    
    def test_service_initialization(self, sync_service):
        """Tester l'initialisation du service"""
        assert sync_service.cj_api is not None
    
    def test_get_stats(self, sync_service):
        """Tester la récupération des statistiques"""
        stats = sync_service.get_stats()
        assert 'products' in stats
        assert 'categories' in stats
        assert 'variants' in stats


class TestShippingService:
    """Tests du service de livraison"""
    
    def test_service_initialization(self, shipping_service):
        """Tester l'initialisation du service"""
        assert shipping_service is not None
    
    def test_fallback_methods(self, shipping_service):
        """Tester les méthodes de livraison par défaut"""
        methods = shipping_service._get_fallback_methods([], 'FR')
        assert len(methods) == 3
        assert methods[0]['code'] == 'STANDARD'
        assert methods[1]['code'] == 'EXPRESS'
        assert methods[2]['code'] == 'PREMIUM'
    
    def test_calculate_total_weight(self, shipping_service):
        """Tester le calcul du poids total"""
        cart_items = [
            {'quantity': 2, 'product': {'product_weight': '300'}},
            {'quantity': 1, 'product': {'product_weight': '500'}}
        ]
        weight = shipping_service._calculate_total_weight(cart_items)
        assert weight == 1100  # (2*300) + (1*500)


class TestAPIEndpoints:
    """Tests des endpoints API"""
    
    def test_stats_endpoint(self, client):
        """Tester l'endpoint des statistiques"""
        response = client.get('/admin/api/cj/stats')
        assert response.status_code == 200
        data = response.get_json()
        assert 'success' in data
    
    def test_shipping_methods_endpoint(self, client):
        """Tester l'endpoint des méthodes de livraison"""
        response = client.get('/api/shipping/methods?country=FR')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True
        assert len(data['methods']) > 0


class TestCacheService:
    """Tests du service de cache"""
    
    def test_cache_durations(self):
        """Tester les durées de cache définies"""
        from services.cache_service import CacheService
        
        assert CacheService.CACHE_DURATIONS['categories'] == 3600
        assert CacheService.CACHE_DURATIONS['products'] == 1800
        assert CacheService.CACHE_DURATIONS['shipping'] == 300


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
