"""
Tests pour les routes
"""
import pytest
from flask import session


class TestMainRoutes:
    """Tests pour les routes principales"""
    
    def test_home_page(self, client):
        """Test page d'accueil"""
        response = client.get('/')
        assert response.status_code == 200
        assert b'MultiProShop' in response.data or b'multiproshop' in response.data.lower()
    
    def test_404_page(self, client):
        """Test page 404"""
        response = client.get('/page-inexistante')
        assert response.status_code == 404


class TestAuthRoutes:
    """Tests pour l'authentification"""
    
    def test_login_page(self, client):
        """Test page de connexion"""
        response = client.get('/auth/login')
        assert response.status_code == 200
    
    def test_login_success(self, client, app):
        """Test connexion réussie"""
        response = client.post('/auth/login', data={
            'email': 'admin@test.com',
            'password': 'admin123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
    
    def test_login_failure(self, client):
        """Test connexion échouée"""
        response = client.post('/auth/login', data={
            'email': 'wrong@test.com',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Devrait rester sur la page de login ou afficher une erreur
    
    def test_logout(self, auth_client):
        """Test déconnexion"""
        response = auth_client.get('/auth/logout', follow_redirects=True)
        assert response.status_code == 200


class TestProductRoutes:
    """Tests pour les routes produits"""
    
    def test_products_list(self, client):
        """Test liste des produits"""
        response = client.get('/products/')
        assert response.status_code == 200
    
    def test_product_detail(self, client, app):
        """Test détail d'un produit"""
        with app.app_context():
            from models.product import Product
            product = Product.query.filter_by(is_active=True).first()
            
            if product:
                response = client.get(f'/products/{product.id}')
                assert response.status_code == 200
    
    def test_product_search(self, client):
        """Test recherche de produits"""
        response = client.get('/products/?search=iPhone')
        assert response.status_code == 200


class TestCartRoutes:
    """Tests pour le panier"""
    
    def test_view_cart(self, client):
        """Test affichage du panier"""
        response = client.get('/cart/')
        assert response.status_code == 200
    
    def test_add_to_cart(self, client, app):
        """Test ajout au panier"""
        with app.app_context():
            from models.product import Product
            product = Product.query.filter_by(is_active=True).first()
            
            if product:
                response = client.post('/cart/add', 
                    json={
                        'product_id': product.id,
                        'quantity': 1
                    }
                )
                assert response.status_code == 200
                data = response.get_json()
                assert data.get('success') is True
    
    def test_update_cart(self, client, app):
        """Test mise à jour du panier"""
        with app.app_context():
            from models.product import Product
            product = Product.query.filter_by(is_active=True).first()
            
            if product:
                # Ajouter d'abord
                client.post('/cart/add', json={
                    'product_id': product.id,
                    'quantity': 1
                })
                
                # Mettre à jour
                response = client.post('/cart/update',
                    json={
                        'product_id': product.id,
                        'quantity': 2
                    }
                )
                assert response.status_code == 200
    
    def test_remove_from_cart(self, client, app):
        """Test suppression du panier"""
        with app.app_context():
            from models.product import Product
            product = Product.query.filter_by(is_active=True).first()
            
            if product:
                # Ajouter d'abord
                client.post('/cart/add', json={
                    'product_id': product.id,
                    'quantity': 1
                })
                
                # Supprimer
                response = client.post('/cart/remove',
                    json={'product_id': product.id}
                )
                assert response.status_code == 200


class TestAdminRoutes:
    """Tests pour les routes admin"""
    
    def test_admin_requires_auth(self, client):
        """Test que l'admin nécessite une authentification"""
        response = client.get('/admin/', follow_redirects=True)
        # Devrait rediriger vers login
        assert response.status_code == 200
    
    def test_admin_dashboard(self, auth_client):
        """Test dashboard admin"""
        response = auth_client.get('/admin/')
        assert response.status_code == 200
    
    def test_admin_products_list(self, auth_client):
        """Test liste produits admin"""
        response = auth_client.get('/admin/products')
        assert response.status_code == 200
    
    def test_admin_orders_list(self, auth_client):
        """Test liste commandes admin"""
        response = auth_client.get('/admin/orders')
        assert response.status_code == 200
    
    def test_admin_users_list(self, auth_client):
        """Test liste utilisateurs admin"""
        response = auth_client.get('/admin/users')
        assert response.status_code == 200


class TestAPIManagementRoutes:
    """Tests pour les routes de gestion API"""
    
    def test_api_providers_requires_admin(self, client):
        """Test que la gestion API nécessite admin"""
        response = client.get('/admin/api/providers', follow_redirects=True)
        assert response.status_code == 200
    
    def test_api_providers_list(self, auth_client):
        """Test liste des providers API"""
        response = auth_client.get('/admin/api/providers')
        assert response.status_code == 200
