"""
Tests pour les modèles
"""
import pytest
from models.user import User
from models.product import Product
from models.category import Category
from models.order import Order
from extensions import db


class TestUserModel:
    """Tests pour le modèle User"""
    
    def test_user_creation(self, app):
        """Test création d'un utilisateur"""
        with app.app_context():
            user = User(
                username='testuser',
                email='test@example.com',
                role_id=2
            )
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
            
            assert user.id is not None
            assert user.username == 'testuser'
            assert user.email == 'test@example.com'
            assert user.password_hash is not None
    
    def test_password_hashing(self, app):
        """Test hashage du mot de passe"""
        with app.app_context():
            user = User(username='test', email='test@test.com', role_id=2)
            user.set_password('secret')
            
            assert user.password_hash != 'secret'
            assert user.check_password('secret') is True
            assert user.check_password('wrong') is False
    
    def test_user_role_relationship(self, app):
        """Test relation User-Role"""
        with app.app_context():
            user = User.query.filter_by(username='admin').first()
            
            assert user is not None
            assert user.role is not None
            assert user.role.name == 'admin'


class TestProductModel:
    """Tests pour le modèle Product"""
    
    def test_product_creation(self, app):
        """Test création d'un produit"""
        with app.app_context():
            category = Category.query.first()
            product = Product(
                name='Test Product',
                description='Test description',
                price=29.99,
                stock=100,
                category_id=category.id,
                is_active=True
            )
            db.session.add(product)
            db.session.commit()
            
            assert product.id is not None
            assert product.name == 'Test Product'
            assert product.price == 29.99
            assert product.stock == 100
    
    def test_product_category_relationship(self, app):
        """Test relation Product-Category"""
        with app.app_context():
            product = Product.query.filter_by(name='iPhone 13').first()
            
            assert product is not None
            assert product.category is not None
            assert product.category.name == 'Électronique'
    
    def test_product_active_filter(self, app):
        """Test filtrage des produits actifs"""
        with app.app_context():
            active_products = Product.query.filter_by(is_active=True).all()
            inactive_products = Product.query.filter_by(is_active=False).all()
            
            assert len(active_products) >= 2
            assert len(inactive_products) >= 1


class TestCategoryModel:
    """Tests pour le modèle Category"""
    
    def test_category_creation(self, app):
        """Test création d'une catégorie"""
        with app.app_context():
            category = Category(
                name='Test Category',
                slug='test-category',
                level=1
            )
            db.session.add(category)
            db.session.commit()
            
            assert category.id is not None
            assert category.name == 'Test Category'
            assert category.slug == 'test-category'
    
    def test_category_products_relationship(self, app):
        """Test relation Category-Products"""
        with app.app_context():
            category = Category.query.filter_by(name='Électronique').first()
            
            assert category is not None
            assert len(category.products) >= 1
            assert any(p.name == 'iPhone 13' for p in category.products)
    
    def test_category_hierarchy(self, app):
        """Test hiérarchie des catégories"""
        with app.app_context():
            parent = Category(name='Parent', slug='parent', level=1)
            db.session.add(parent)
            db.session.flush()
            
            child = Category(
                name='Child',
                slug='child',
                level=2,
                parent_id=parent.id
            )
            db.session.add(child)
            db.session.commit()
            
            assert child.parent_id == parent.id
            assert parent.id is not None


class TestOrderModel:
    """Tests pour le modèle Order"""
    
    def test_order_creation(self, app):
        """Test création d'une commande"""
        with app.app_context():
            user = User.query.filter_by(username='client').first()
            
            order = Order(
                user_id=user.id,
                total_amount=99.99,
                status='pending',
                payment_status='pending',
                customer_name='Test Client',
                customer_email='client@test.com',
                shipping_address='123 Test St',
                shipping_city='Test City',
                shipping_postal_code='12345',
                shipping_country='France'
            )
            db.session.add(order)
            db.session.commit()
            
            assert order.id is not None
            assert order.order_number is not None
            assert order.total_amount == 99.99
            assert order.status == 'pending'
    
    def test_order_user_relationship(self, app):
        """Test relation Order-User"""
        with app.app_context():
            user = User.query.filter_by(username='client').first()
            
            order = Order(
                user_id=user.id,
                total_amount=50.00,
                status='pending',
                payment_status='pending',
                customer_name='Test',
                customer_email='test@test.com',
                shipping_address='Address',
                shipping_city='City',
                shipping_postal_code='12345',
                shipping_country='France'
            )
            db.session.add(order)
            db.session.commit()
            
            assert order.user is not None
            assert order.user.username == 'client'
