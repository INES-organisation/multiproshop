"""
Tests automatiques pour les fonctions critiques CJ Dropshipping
Teste les fonctionnalités essentielles pour garantir la stabilité
"""
import unittest
import sys
import os
from datetime import datetime
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from extensions import db
from models.product import Product
from models.product_variant import ProductVariant
from models.category import Category
from models.order import Order
from services.pricing_service import PricingService


class TestCJCriticalFunctions(unittest.TestCase):
    """Tests pour les fonctions critiques CJ"""
    
    @classmethod
    def setUpClass(cls):
        """Configuration initiale des tests"""
        cls.app = app
        cls.app.config['TESTING'] = True
        cls.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        with cls.app.app_context():
            db.create_all()
            
            # Créer une catégorie de test
            cls.test_category = Category(
                name='Test Category',
                slug='test-category',
                cj_category_id='TEST_CAT_001',
                level=1,
                visible=True
            )
            db.session.add(cls.test_category)
            db.session.commit()
    
    @classmethod
    def tearDownClass(cls):
        """Nettoyage après les tests"""
        with cls.app.app_context():
            db.session.remove()
            db.drop_all()
    
    def setUp(self):
        """Configuration avant chaque test"""
        self.ctx = self.app.app_context()
        self.ctx.push()
    
    def tearDown(self):
        """Nettoyage après chaque test"""
        db.session.rollback()
        self.ctx.pop()
    
    # ==================== TESTS PRODUITS ====================
    
    def test_product_creation_with_cj_data(self):
        """Test: Création d'un produit avec données CJ"""
        product = Product(
            name='Test Product CJ',
            slug='test-product-cj',
            cj_pid='TEST_PID_001',
            price=29.99,
            stock=100,
            category_id=self.test_category.id,
            cj_raw_data=json.dumps({'test': 'data'}),
            cj_last_sync=datetime.utcnow()
        )
        
        db.session.add(product)
        db.session.commit()
        
        # Vérifications
        self.assertIsNotNone(product.id)
        self.assertEqual(product.cj_pid, 'TEST_PID_001')
        self.assertIsNotNone(product.cj_raw_data)
        self.assertIsNotNone(product.cj_last_sync)
        
        # Vérifier que les données JSON sont valides
        raw_data = json.loads(product.cj_raw_data)
        self.assertEqual(raw_data['test'], 'data')
    
    def test_product_unique_cj_pid(self):
        """Test: Unicité du cj_pid"""
        product1 = Product(
            name='Product 1',
            slug='product-1',
            cj_pid='UNIQUE_PID_001',
            price=19.99,
            stock=50,
            category_id=self.test_category.id
        )
        db.session.add(product1)
        db.session.commit()
        
        # Tenter de créer un produit avec le même cj_pid
        product2 = Product(
            name='Product 2',
            slug='product-2',
            cj_pid='UNIQUE_PID_001',  # Même PID
            price=29.99,
            stock=30,
            category_id=self.test_category.id
        )
        db.session.add(product2)
        
        # Doit lever une exception
        with self.assertRaises(Exception):
            db.session.commit()
    
    def test_product_stock_management(self):
        """Test: Gestion du stock produit"""
        product = Product(
            name='Stock Test Product',
            slug='stock-test-product',
            cj_pid='STOCK_TEST_001',
            price=39.99,
            stock=100,
            low_stock_threshold=10,
            category_id=self.test_category.id
        )
        db.session.add(product)
        db.session.commit()
        
        # Test stock initial
        self.assertEqual(product.stock, 100)
        
        # Simuler une vente
        product.stock -= 5
        db.session.commit()
        self.assertEqual(product.stock, 95)
        
        # Vérifier seuil bas
        product.stock = 8
        db.session.commit()
        self.assertTrue(product.stock < product.low_stock_threshold)
    
    # ==================== TESTS VARIANTES ====================
    
    def test_variant_creation_with_cj_data(self):
        """Test: Création d'une variante avec données CJ"""
        product = Product(
            name='Variant Test Product',
            slug='variant-test-product',
            cj_pid='VARIANT_TEST_001',
            price=49.99,
            stock=0,
            category_id=self.test_category.id
        )
        db.session.add(product)
        db.session.flush()
        
        variant = ProductVariant(
            product_id=product.id,
            cj_vid='VARIANT_VID_001',
            variant_key='Red-M',
            color='Red',
            size='M',
            price=49.99,
            stock=25,
            cj_raw_data=json.dumps({'color_code': '#FF0000'})
        )
        db.session.add(variant)
        db.session.commit()
        
        # Vérifications
        self.assertIsNotNone(variant.id)
        self.assertEqual(variant.cj_vid, 'VARIANT_VID_001')
        self.assertEqual(variant.color, 'Red')
        self.assertEqual(variant.size, 'M')
        self.assertIsNotNone(variant.cj_raw_data)
        
        # Vérifier données JSON
        raw_data = json.loads(variant.cj_raw_data)
        self.assertEqual(raw_data['color_code'], '#FF0000')
    
    def test_variant_unique_cj_vid(self):
        """Test: Unicité du cj_vid"""
        product = Product(
            name='Variant Unique Test',
            slug='variant-unique-test',
            cj_pid='VARIANT_UNIQUE_001',
            price=59.99,
            stock=0,
            category_id=self.test_category.id
        )
        db.session.add(product)
        db.session.flush()
        
        variant1 = ProductVariant(
            product_id=product.id,
            cj_vid='UNIQUE_VID_001',
            variant_key='Blue-S',
            price=59.99,
            stock=10
        )
        db.session.add(variant1)
        db.session.commit()
        
        # Tenter de créer une variante avec le même cj_vid
        variant2 = ProductVariant(
            product_id=product.id,
            cj_vid='UNIQUE_VID_001',  # Même VID
            variant_key='Blue-M',
            price=59.99,
            stock=15
        )
        db.session.add(variant2)
        
        # Doit lever une exception
        with self.assertRaises(Exception):
            db.session.commit()
    
    # ==================== TESTS PRICING ====================
    
    def test_pricing_calculation(self):
        """Test: Calcul des prix avec marge"""
        pricing_service = PricingService()
        
        # Test calcul prix de vente
        cj_price = 10.0
        markup = 60  # 60% de marge
        
        selling_price = pricing_service.calculate_selling_price(cj_price, markup)
        
        # Prix de vente = 10 * (1 + 0.60) = 16.0
        self.assertEqual(selling_price, 16.0)
    
    def test_pricing_rounding(self):
        """Test: Arrondi psychologique des prix"""
        pricing_service = PricingService()
        
        # Test avec arrondi .99
        price = pricing_service.apply_psychological_rounding(15.50)
        self.assertEqual(price, 15.99)
        
        price = pricing_service.apply_psychological_rounding(20.00)
        self.assertEqual(price, 19.99)
    
    # ==================== TESTS COMMANDES ====================
    
    def test_order_with_cj_data(self):
        """Test: Création d'une commande avec données CJ"""
        order = Order(
            order_number='TEST_ORDER_001',
            user_id=1,
            status='paid',
            total_amount=99.99,
            cj_order_id='CJ_ORDER_001',
            cj_status='PENDING',
            customer_name='Test Customer',
            customer_email='test@example.com'
        )
        db.session.add(order)
        db.session.commit()
        
        # Vérifications
        self.assertIsNotNone(order.id)
        self.assertEqual(order.cj_order_id, 'CJ_ORDER_001')
        self.assertEqual(order.cj_status, 'PENDING')
    
    def test_order_status_mapping(self):
        """Test: Mapping des statuts CJ vers statuts locaux"""
        order = Order(
            order_number='TEST_ORDER_002',
            user_id=1,
            status='paid',
            total_amount=149.99,
            cj_order_id='CJ_ORDER_002',
            customer_name='Test Customer 2',
            customer_email='test2@example.com'
        )
        db.session.add(order)
        db.session.commit()
        
        # Simuler changement de statut
        order.status = 'shipped'
        order.cj_status = 'SHIPPED'
        db.session.commit()
        
        self.assertEqual(order.status, 'shipped')
        self.assertEqual(order.cj_status, 'SHIPPED')
    
    # ==================== TESTS CATÉGORIES ====================
    
    def test_category_hierarchy(self):
        """Test: Hiérarchie des catégories"""
        parent = Category(
            name='Parent Category',
            slug='parent-category',
            cj_category_id='PARENT_001',
            level=1,
            visible=True
        )
        db.session.add(parent)
        db.session.flush()
        
        child = Category(
            name='Child Category',
            slug='child-category',
            cj_category_id='CHILD_001',
            level=2,
            parent_id=parent.id,
            visible=True
        )
        db.session.add(child)
        db.session.commit()
        
        # Vérifications
        self.assertEqual(child.parent_id, parent.id)
        self.assertEqual(child.level, 2)
        self.assertEqual(parent.level, 1)
    
    def test_category_product_count(self):
        """Test: Compteur de produits par catégorie"""
        category = Category(
            name='Count Test Category',
            slug='count-test-category',
            cj_category_id='COUNT_TEST_001',
            level=1,
            visible=True,
            product_count=0
        )
        db.session.add(category)
        db.session.flush()
        
        # Ajouter des produits
        for i in range(5):
            product = Product(
                name=f'Product {i}',
                slug=f'product-{i}',
                cj_pid=f'COUNT_PID_{i:03d}',
                price=19.99,
                stock=10,
                category_id=category.id
            )
            db.session.add(product)
        
        db.session.commit()
        
        # Compter les produits
        actual_count = Product.query.filter_by(category_id=category.id).count()
        self.assertEqual(actual_count, 5)
    
    # ==================== TESTS INTÉGRITÉ ====================
    
    def test_data_integrity_product_variant(self):
        """Test: Intégrité des données produit-variante"""
        product = Product(
            name='Integrity Test Product',
            slug='integrity-test-product',
            cj_pid='INTEGRITY_TEST_001',
            price=79.99,
            stock=0,
            category_id=self.test_category.id
        )
        db.session.add(product)
        db.session.flush()
        
        # Ajouter variantes
        variants_data = [
            {'color': 'Red', 'size': 'S', 'stock': 10},
            {'color': 'Red', 'size': 'M', 'stock': 15},
            {'color': 'Blue', 'size': 'S', 'stock': 8},
        ]
        
        for i, vdata in enumerate(variants_data):
            variant = ProductVariant(
                product_id=product.id,
                cj_vid=f'INTEGRITY_VID_{i:03d}',
                variant_key=f"{vdata['color']}-{vdata['size']}",
                color=vdata['color'],
                size=vdata['size'],
                price=79.99,
                stock=vdata['stock']
            )
            db.session.add(variant)
        
        db.session.commit()
        
        # Vérifier que toutes les variantes sont liées au produit
        variants = ProductVariant.query.filter_by(product_id=product.id).all()
        self.assertEqual(len(variants), 3)
        
        # Vérifier stock total
        total_stock = sum(v.stock for v in variants)
        self.assertEqual(total_stock, 33)


def run_tests():
    """Exécuter tous les tests"""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestCJCriticalFunctions)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
