"""
Tests d'intégration pour MultiProShop
Phase 4 - Tests E2E et intégration
"""
import unittest
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from extensions import db
from models.product import Product
from models.category import Category
from models.user import User


class TestProductIntegration(unittest.TestCase):
    """Tests d'intégration pour les produits"""
    
    def setUp(self):
        """Configuration avant chaque test"""
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
    
    def tearDown(self):
        """Nettoyage après chaque test"""
        self.app_context.pop()
    
    def test_homepage_loads(self):
        """Test que la page d'accueil se charge"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'MultiProShop', response.data)
    
    def test_products_list_loads(self):
        """Test que la liste des produits se charge"""
        response = self.client.get('/products/')
        self.assertEqual(response.status_code, 200)
    
    def test_product_detail_loads(self):
        """Test qu'une page produit se charge"""
        # Récupérer un produit actif
        product = Product.query.filter(Product.is_active == True).first()
        
        if product:
            response = self.client.get(f'/products/{product.id}')
            self.assertIn(response.status_code, [200, 302])
    
    def test_search_page_loads(self):
        """Test que la page de recherche se charge"""
        response = self.client.get('/search')
        self.assertEqual(response.status_code, 200)
    
    def test_search_with_query(self):
        """Test recherche avec query"""
        response = self.client.get('/search?q=test')
        self.assertEqual(response.status_code, 200)
    
    def test_search_api_suggestions(self):
        """Test API suggestions de recherche"""
        response = self.client.get('/search/api/suggestions?q=mat')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('suggestions', data)
        self.assertIsInstance(data['suggestions'], list)


class TestCJDashboardIntegration(unittest.TestCase):
    """Tests d'intégration pour le dashboard CJ"""
    
    def setUp(self):
        """Configuration avant chaque test"""
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
    
    def tearDown(self):
        """Nettoyage après chaque test"""
        self.app_context.pop()
    
    def test_dashboard_accessible(self):
        """Test que le dashboard est accessible"""
        response = self.client.get('/admin/cj/dashboard')
        # Peut être 200 (accessible) ou 302 (redirect login)
        self.assertIn(response.status_code, [200, 302, 401])


class TestAPIEndpoints(unittest.TestCase):
    """Tests des endpoints API"""
    
    def setUp(self):
        """Configuration avant chaque test"""
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
    
    def tearDown(self):
        """Nettoyage après chaque test"""
        self.app_context.pop()
    
    def test_api_search_suggestions(self):
        """Test API suggestions"""
        response = self.client.get('/search/api/suggestions?q=test')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIsInstance(data, dict)
    
    def test_api_popular_searches(self):
        """Test API recherches populaires"""
        response = self.client.get('/search/api/popular')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('popular', data)


class TestWorkflow(unittest.TestCase):
    """Tests de workflow complet"""
    
    def setUp(self):
        """Configuration avant chaque test"""
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
    
    def tearDown(self):
        """Nettoyage après chaque test"""
        self.app_context.pop()
    
    def test_search_to_product_workflow(self):
        """Test workflow: recherche → produit"""
        # 1. Rechercher
        response = self.client.get('/search?q=keyboard')
        self.assertEqual(response.status_code, 200)
        
        # 2. Récupérer un produit
        product = Product.query.filter(
            Product.name.ilike('%keyboard%'),
            Product.is_active == True
        ).first()
        
        if product:
            # 3. Voir le produit
            response = self.client.get(f'/products/{product.id}')
            self.assertIn(response.status_code, [200, 302])
    
    def test_homepage_to_products_workflow(self):
        """Test workflow: accueil → produits"""
        # 1. Page d'accueil
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        
        # 2. Liste produits
        response = self.client.get('/products/')
        self.assertEqual(response.status_code, 200)


def run_integration_tests():
    """Exécuter tous les tests d'intégration"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Ajouter les tests
    suite.addTests(loader.loadTestsFromTestCase(TestProductIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestCJDashboardIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestAPIEndpoints))
    suite.addTests(loader.loadTestsFromTestCase(TestWorkflow))
    
    # Exécuter
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_integration_tests())
