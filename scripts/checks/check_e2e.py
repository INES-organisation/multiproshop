"""
Tests End-to-End avec Playwright
Phase 4 - Tests E2E complets
"""
import unittest
import sys
import os
import time
from urllib.parse import urljoin

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestE2EHomepage(unittest.TestCase):
    """Tests E2E pour la page d'accueil"""
    
    @classmethod
    def setUpClass(cls):
        """Configuration avant tous les tests"""
        cls.base_url = 'http://multiproshop.local'
    
    def test_homepage_loads(self):
        """Test que la page d'accueil se charge"""
        import requests
        
        response = requests.get(self.base_url, timeout=10)
        self.assertEqual(response.status_code, 200)
        self.assertIn('MultiProShop', response.text)
    
    def test_homepage_has_navigation(self):
        """Test que la navigation est présente"""
        import requests
        
        response = requests.get(self.base_url, timeout=10)
        self.assertIn('nav', response.text.lower())


class TestE2ESearch(unittest.TestCase):
    """Tests E2E pour la recherche"""
    
    @classmethod
    def setUpClass(cls):
        """Configuration avant tous les tests"""
        cls.base_url = 'http://multiproshop.local'
    
    def test_search_page_loads(self):
        """Test que la page de recherche se charge"""
        import requests
        
        url = urljoin(self.base_url, '/search')
        response = requests.get(url, timeout=10)
        self.assertEqual(response.status_code, 200)
    
    def test_search_with_query(self):
        """Test recherche avec un terme"""
        import requests
        
        url = urljoin(self.base_url, '/search?q=keyboard')
        response = requests.get(url, timeout=10)
        self.assertEqual(response.status_code, 200)
        self.assertIn('keyboard', response.text.lower())
    
    def test_search_api_suggestions(self):
        """Test API suggestions"""
        import requests
        
        url = urljoin(self.base_url, '/search/api/suggestions?q=key')
        response = requests.get(url, timeout=10)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('suggestions', data)


class TestE2EProducts(unittest.TestCase):
    """Tests E2E pour les produits"""
    
    @classmethod
    def setUpClass(cls):
        """Configuration avant tous les tests"""
        cls.base_url = 'http://multiproshop.local'
    
    def test_products_list_loads(self):
        """Test que la liste des produits se charge"""
        import requests
        
        url = urljoin(self.base_url, '/products/')
        response = requests.get(url, timeout=10)
        self.assertIn(response.status_code, [200, 302])
    
    def test_product_detail_loads(self):
        """Test qu'une page produit se charge"""
        import requests
        
        # Tester avec ID 1
        url = urljoin(self.base_url, '/products/1')
        response = requests.get(url, timeout=10)
        self.assertIn(response.status_code, [200, 302, 404])


class TestE2EWorkflow(unittest.TestCase):
    """Tests E2E de workflows complets"""
    
    @classmethod
    def setUpClass(cls):
        """Configuration avant tous les tests"""
        cls.base_url = 'http://multiproshop.local'
    
    def test_homepage_to_search_workflow(self):
        """Test workflow: accueil → recherche → résultats"""
        import requests
        
        # 1. Charger page d'accueil
        response = requests.get(self.base_url, timeout=10)
        self.assertEqual(response.status_code, 200)
        
        # 2. Faire une recherche
        url = urljoin(self.base_url, '/search?q=test')
        response = requests.get(url, timeout=10)
        self.assertEqual(response.status_code, 200)
    
    def test_search_to_product_workflow(self):
        """Test workflow: recherche → produit"""
        import requests
        from models.product import Product
        from app import create_app
        
        # Récupérer un produit via l'app
        app = create_app('testing')
        with app.app_context():
            product = Product.query.filter(Product.is_active == True).first()
            
            if product:
                # Accéder à la page produit
                url = urljoin(self.base_url, f'/products/{product.id}')
                response = requests.get(url, timeout=10)
                self.assertIn(response.status_code, [200, 302])


class TestE2EAdmin(unittest.TestCase):
    """Tests E2E pour l'admin"""
    
    @classmethod
    def setUpClass(cls):
        """Configuration avant tous les tests"""
        cls.base_url = 'http://multiproshop.local'
    
    def test_admin_dashboard_accessible(self):
        """Test que le dashboard admin est accessible"""
        import requests
        
        url = urljoin(self.base_url, '/admin/cj/dashboard')
        response = requests.get(url, timeout=10)
        # Peut être 200 (accessible) ou 302 (redirect login) ou 401 (non autorisé)
        self.assertIn(response.status_code, [200, 302, 401])


class TestE2EAPI(unittest.TestCase):
    """Tests E2E pour l'API"""
    
    @classmethod
    def setUpClass(cls):
        """Configuration avant tous les tests"""
        cls.base_url = 'http://multiproshop.local'
    
    def test_health_endpoint(self):
        """Test endpoint health"""
        import requests
        
        url = urljoin(self.base_url, '/health')
        response = requests.get(url, timeout=10)
        self.assertIn(response.status_code, [200, 503])
        
        data = response.json()
        self.assertIn('status', data)
    
    def test_metrics_endpoint(self):
        """Test endpoint metrics"""
        import requests
        
        url = urljoin(self.base_url, '/metrics')
        response = requests.get(url, timeout=10)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('system', data)
    
    def test_sitemap_endpoint(self):
        """Test endpoint sitemap"""
        import requests
        
        url = urljoin(self.base_url, '/sitemap.xml')
        response = requests.get(url, timeout=10)
        self.assertEqual(response.status_code, 200)
        self.assertIn('xml', response.headers.get('Content-Type', ''))
    
    def test_robots_endpoint(self):
        """Test endpoint robots"""
        import requests
        
        url = urljoin(self.base_url, '/robots.txt')
        response = requests.get(url, timeout=10)
        self.assertEqual(response.status_code, 200)
        self.assertIn('User-agent', response.text)


class TestE2EPerformance(unittest.TestCase):
    """Tests E2E de performance"""
    
    @classmethod
    def setUpClass(cls):
        """Configuration avant tous les tests"""
        cls.base_url = 'http://multiproshop.local'
    
    def test_homepage_load_time(self):
        """Test temps de chargement page d'accueil"""
        import requests
        
        start = time.time()
        response = requests.get(self.base_url, timeout=10)
        load_time = time.time() - start
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(load_time, 5.0, "Page d'accueil trop lente (>5s)")
    
    def test_search_response_time(self):
        """Test temps de réponse recherche"""
        import requests
        
        url = urljoin(self.base_url, '/search?q=test')
        
        start = time.time()
        response = requests.get(url, timeout=10)
        response_time = time.time() - start
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(response_time, 2.0, "Recherche trop lente (>2s)")


def run_e2e_tests():
    """Exécuter tous les tests E2E"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Ajouter les tests
    suite.addTests(loader.loadTestsFromTestCase(TestE2EHomepage))
    suite.addTests(loader.loadTestsFromTestCase(TestE2ESearch))
    suite.addTests(loader.loadTestsFromTestCase(TestE2EProducts))
    suite.addTests(loader.loadTestsFromTestCase(TestE2EWorkflow))
    suite.addTests(loader.loadTestsFromTestCase(TestE2EAdmin))
    suite.addTests(loader.loadTestsFromTestCase(TestE2EAPI))
    suite.addTests(loader.loadTestsFromTestCase(TestE2EPerformance))
    
    # Exécuter
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    print("\n" + "="*70)
    print("  TESTS END-TO-END MULTIPROSHOP")
    print("  Phase 4 - Tests E2E complets")
    print("="*70 + "\n")
    
    sys.exit(run_e2e_tests())
