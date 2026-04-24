"""
Tests de performance automatisés pour MultiProShop
Vérifie que les optimisations sont maintenues
"""
import pytest
import time
from app import create_app
from extensions import db
from models.product import Product
from models.category import Category

@pytest.fixture
def app():
    """Créer l'application de test"""
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """Client de test"""
    return app.test_client()

class TestPerformance:
    """Tests de performance"""
    
    def test_homepage_load_time(self, client):
        """Vérifier que la page d'accueil charge en moins de 500ms"""
        start = time.time()
        response = client.get('/')
        duration = time.time() - start
        
        assert response.status_code == 200
        assert duration < 0.5, f"Page d'accueil trop lente: {duration:.3f}s"
    
    def test_product_list_load_time(self, client):
        """Vérifier que la liste des produits charge rapidement"""
        start = time.time()
        response = client.get('/products')
        duration = time.time() - start
        
        assert response.status_code == 200
        assert duration < 0.5, f"Liste produits trop lente: {duration:.3f}s"
    
    def test_database_query_count(self, app):
        """Vérifier que le nombre de requêtes DB est minimal"""
        from flask_sqlalchemy import get_debug_queries
        
        with app.test_client() as client:
            # Activer le tracking des requêtes
            app.config['SQLALCHEMY_RECORD_QUERIES'] = True
            
            response = client.get('/')
            
            queries = get_debug_queries()
            query_count = len(queries)
            
            assert query_count < 10, f"Trop de requêtes DB: {query_count}"
    
    def test_cache_effectiveness(self, app, client):
        """Vérifier que le cache fonctionne"""
        # Première requête (pas en cache)
        start1 = time.time()
        response1 = client.get('/')
        duration1 = time.time() - start1
        
        # Deuxième requête (en cache)
        start2 = time.time()
        response2 = client.get('/')
        duration2 = time.time() - start2
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # La deuxième requête devrait être plus rapide
        assert duration2 < duration1, "Le cache ne semble pas fonctionner"
    
    def test_eager_loading_no_n_plus_1(self, app):
        """Vérifier qu'il n'y a pas de requêtes N+1"""
        with app.app_context():
            # Créer des données de test
            category = Category(name='Test', level=1, is_active=True)
            db.session.add(category)
            db.session.commit()
            
            for i in range(10):
                product = Product(
                    name=f'Product {i}',
                    price=10.0,
                    category_id=category.id,
                    is_active=True
                )
                db.session.add(product)
            db.session.commit()
            
            # Activer le tracking
            app.config['SQLALCHEMY_RECORD_QUERIES'] = True
            
            from services.product_service import ProductService
            from flask_sqlalchemy import get_debug_queries
            
            # Récupérer les produits
            products = ProductService.get_products_by_category(category.id)
            
            # Accéder aux catégories (devrait être en eager loading)
            for product in products:
                _ = product.category.name
            
            queries = get_debug_queries()
            
            # Devrait avoir 1-2 requêtes max (pas 11 = 1 + 10)
            assert len(queries) <= 2, f"Requêtes N+1 détectées: {len(queries)} requêtes"
    
    def test_response_headers(self, client):
        """Vérifier que les headers de performance sont présents"""
        response = client.get('/')
        
        # Vérifier X-Response-Time
        assert 'X-Response-Time' in response.headers
        
        # Vérifier que le temps est raisonnable
        response_time = float(response.headers['X-Response-Time'].replace('ms', ''))
        assert response_time < 500, f"Temps de réponse trop élevé: {response_time}ms"
    
    def test_service_worker_available(self, client):
        """Vérifier que le Service Worker est disponible"""
        response = client.get('/static/js/sw.js')
        assert response.status_code == 200
        assert b'Service Worker' in response.data


class TestDatabasePerformance:
    """Tests de performance de la base de données"""
    
    def test_indexes_exist(self, app):
        """Vérifier que les index sont créés"""
        with app.app_context():
            from sqlalchemy import inspect
            
            inspector = inspect(db.engine)
            
            # Vérifier les index sur product
            product_indexes = inspector.get_indexes('product')
            index_names = [idx['name'] for idx in product_indexes]
            
            assert 'idx_product_category_active' in index_names
            assert 'idx_product_published' in index_names
    
    def test_connection_pool_configured(self, app):
        """Vérifier que le connection pool est configuré"""
        assert app.config['SQLALCHEMY_ENGINE_OPTIONS']['pool_size'] == 10
        assert app.config['SQLALCHEMY_ENGINE_OPTIONS']['max_overflow'] == 20


class TestCachePerformance:
    """Tests de performance du cache"""
    
    def test_redis_connection(self, app):
        """Vérifier que Redis est accessible"""
        from extensions import cache
        
        with app.app_context():
            # Tester set/get
            cache.set('test_key', 'test_value', timeout=10)
            value = cache.get('test_key')
            
            assert value == 'test_value'
    
    def test_context_processor_cached(self, app, client):
        """Vérifier que le context processor utilise le cache"""
        with app.test_client() as client:
            app.config['SQLALCHEMY_RECORD_QUERIES'] = True
            
            # Première requête
            response1 = client.get('/')
            
            # Deuxième requête (devrait utiliser le cache)
            response2 = client.get('/')
            
            from flask_sqlalchemy import get_debug_queries
            queries = get_debug_queries()
            
            # Le nombre de requêtes devrait être minimal grâce au cache
            assert len(queries) < 5


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
