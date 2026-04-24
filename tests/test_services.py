"""
Tests unitaires pour les services principaux
Phase 4 - Tests automatisés
"""
import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from extensions import db
from models.product import Product
from models.category import Category
from services.pricing_service import PricingService
from services.search_service import get_search_service
from services.recommendation_service import get_recommendation_service


class TestPricingService(unittest.TestCase):
    """Tests pour PricingService"""
    
    def setUp(self):
        """Configuration avant chaque test"""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.pricing = PricingService()
    
    def tearDown(self):
        """Nettoyage après chaque test"""
        self.app_context.pop()
    
    def test_calculate_sell_price_default_margin(self):
        """Test calcul prix avec marge par défaut"""
        cj_price = 10.0
        sell_price = self.pricing.calculate_sell_price(cj_price)
        
        # Marge par défaut 40% = prix * 1.4
        expected = 14.0  # 10 * 1.4
        self.assertAlmostEqual(sell_price, expected, places=2)
    
    def test_calculate_sell_price_custom_margin(self):
        """Test calcul prix avec marge personnalisée"""
        cj_price = 20.0
        margin = 50.0  # 50%
        sell_price = self.pricing.calculate_sell_price(cj_price, margin_percent=margin)
        
        expected = 30.0  # 20 * 1.5
        self.assertAlmostEqual(sell_price, expected, places=2)
    
    def test_calculate_compare_price(self):
        """Test calcul prix barré"""
        sell_price = 100.0
        compare_price = self.pricing.calculate_compare_price(sell_price)
        
        # Prix barré = prix * 1.3
        expected = 130.0
        self.assertAlmostEqual(compare_price, expected, places=2)
    
    def test_calculate_profit(self):
        """Test calcul bénéfice"""
        cj_price = 10.0
        sell_price = 15.0
        profit = self.pricing.calculate_profit(cj_price, sell_price)
        
        expected = 5.0
        self.assertAlmostEqual(profit, expected, places=2)
    
    def test_calculate_margin_percent(self):
        """Test calcul pourcentage de marge"""
        cj_price = 10.0
        sell_price = 15.0
        margin = self.pricing.calculate_margin_percent(cj_price, sell_price)
        
        # (15 - 10) / 10 * 100 = 50%
        expected = 50.0
        self.assertAlmostEqual(margin, expected, places=2)
    
    def test_round_price_psychological(self):
        """Test arrondi psychologique (.99)"""
        price = 15.23
        rounded = self.pricing.round_price_psychological(price)
        
        # Devrait arrondir à 14.99
        expected = 14.99
        self.assertAlmostEqual(rounded, expected, places=2)


class TestSearchService(unittest.TestCase):
    """Tests pour SearchService"""
    
    def setUp(self):
        """Configuration avant chaque test"""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.search = get_search_service()
    
    def tearDown(self):
        """Nettoyage après chaque test"""
        self.app_context.pop()
    
    def test_search_products_empty_query(self):
        """Test recherche avec query vide"""
        result = self.search.search_products(query="", page=1, per_page=10)
        
        self.assertTrue(result['success'])
        self.assertIsInstance(result['products'], list)
        self.assertIsInstance(result['total'], int)
    
    def test_search_products_with_query(self):
        """Test recherche avec terme"""
        result = self.search.search_products(query="test", page=1, per_page=10)
        
        self.assertTrue(result['success'])
        self.assertIsInstance(result['products'], list)
        self.assertLessEqual(len(result['products']), 10)
    
    def test_search_with_price_filter(self):
        """Test recherche avec filtre prix"""
        result = self.search.search_products(
            query="",
            min_price=10.0,
            max_price=50.0,
            page=1,
            per_page=10
        )
        
        self.assertTrue(result['success'])
        # Vérifier que les produits sont dans la fourchette
        for product in result['products']:
            self.assertGreaterEqual(product.price, 10.0)
            self.assertLessEqual(product.price, 50.0)
    
    def test_search_with_sort(self):
        """Test recherche avec tri"""
        result = self.search.search_products(
            query="",
            sort_by='price_asc',
            page=1,
            per_page=5
        )
        
        self.assertTrue(result['success'])
        
        # Vérifier que les prix sont triés
        if len(result['products']) > 1:
            prices = [p.price for p in result['products']]
            self.assertEqual(prices, sorted(prices))
    
    def test_get_search_suggestions(self):
        """Test suggestions de recherche"""
        suggestions = self.search.get_search_suggestions("mat", limit=5)
        
        self.assertIsInstance(suggestions, list)
        self.assertLessEqual(len(suggestions), 5)


class TestRecommendationService(unittest.TestCase):
    """Tests pour RecommendationService"""
    
    def setUp(self):
        """Configuration avant chaque test"""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.reco = get_recommendation_service()
    
    def tearDown(self):
        """Nettoyage après chaque test"""
        self.app_context.pop()
    
    def test_get_similar_products(self):
        """Test produits similaires"""
        # Récupérer un produit
        product = Product.query.filter(Product.is_active == True).first()
        
        if product:
            similar = self.reco.get_similar_products(product.id, limit=6)
            
            self.assertIsInstance(similar, list)
            self.assertLessEqual(len(similar), 6)
            
            # Vérifier qu'on ne retourne pas le produit lui-même
            for p in similar:
                self.assertNotEqual(p.id, product.id)
    
    def test_get_trending_products(self):
        """Test produits tendance"""
        trending = self.reco.get_trending_products(limit=8, days=7)
        
        self.assertIsInstance(trending, list)
        self.assertLessEqual(len(trending), 8)
    
    def test_get_new_arrivals(self):
        """Test nouveautés"""
        new_products = self.reco.get_new_arrivals(limit=8)
        
        self.assertIsInstance(new_products, list)
        self.assertLessEqual(len(new_products), 8)
        
        # Vérifier que les produits sont triés par date
        if len(new_products) > 1:
            dates = [p.created_at for p in new_products]
            self.assertEqual(dates, sorted(dates, reverse=True))
    
    def test_get_personalized_recommendations_no_user(self):
        """Test recommandations sans utilisateur"""
        recommendations = self.reco.get_personalized_recommendations(
            user_id=None,
            limit=8
        )
        
        self.assertIsInstance(recommendations, list)
        self.assertLessEqual(len(recommendations), 8)


class TestImageService(unittest.TestCase):
    """Tests pour ImageService"""
    
    def setUp(self):
        """Configuration avant chaque test"""
        from services.image_service import ImageService
        self.image_service = ImageService()
    
    def test_thumbnail_sizes_defined(self):
        """Test que les tailles de miniatures sont définies"""
        self.assertIn('small', self.image_service.thumbnail_sizes)
        self.assertIn('medium', self.image_service.thumbnail_sizes)
        self.assertIn('large', self.image_service.thumbnail_sizes)
    
    def test_base_path_exists(self):
        """Test que le chemin de base existe"""
        self.assertTrue(self.image_service.base_path.exists())


def run_tests():
    """Exécuter tous les tests"""
    # Créer la suite de tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Ajouter les tests
    suite.addTests(loader.loadTestsFromTestCase(TestPricingService))
    suite.addTests(loader.loadTestsFromTestCase(TestSearchService))
    suite.addTests(loader.loadTestsFromTestCase(TestRecommendationService))
    suite.addTests(loader.loadTestsFromTestCase(TestImageService))
    
    # Exécuter
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Retourner le code de sortie
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())
