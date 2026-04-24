"""
Service de gestion du panier
"""
from flask import session
from models.product import Product
from extensions import db


class CartService:
    """Service pour gérer les opérations du panier"""
    
    @staticmethod
    def get_cart():
        """Récupère le panier de la session"""
        return session.get('cart', {})
    
    @staticmethod
    def add_to_cart(product_id, quantity=1):
        """
        Ajoute un produit au panier
        
        Args:
            product_id: ID du produit
            quantity: Quantité à ajouter
            
        Returns:
            tuple: (success: bool, message: str, product: Product or None)
        """
        product = Product.query.get(product_id)
        
        if not product:
            return False, 'Produit introuvable', None
        
        if product.stock < quantity:
            return False, 'Stock insuffisant', product
        
        cart = CartService.get_cart()
        cart[str(product_id)] = cart.get(str(product_id), 0) + quantity
        session['cart'] = cart
        session.modified = True
        
        return True, f'{quantity} {product.name} ajouté(s) au panier', product
    
    @staticmethod
    def remove_from_cart(product_id):
        """
        Retire un produit du panier
        
        Args:
            product_id: ID du produit à retirer
            
        Returns:
            bool: True si le produit a été retiré
        """
        cart = CartService.get_cart()
        if str(product_id) in cart:
            del cart[str(product_id)]
            session['cart'] = cart
            session.modified = True
            return True
        return False
    
    @staticmethod
    def update_quantity(product_id, action):
        """
        Met à jour la quantité d'un produit dans le panier
        
        Args:
            product_id: ID du produit
            action: 'increase' ou 'decrease'
            
        Returns:
            bool: True si la mise à jour a réussi
        """
        cart = CartService.get_cart()
        
        if str(product_id) not in cart:
            return False
        
        current_quantity = cart[str(product_id)]
        
        if action == 'increase':
            product = Product.query.get(product_id)
            if product and product.stock > current_quantity:
                cart[str(product_id)] = current_quantity + 1
            else:
                return False
        elif action == 'decrease' and current_quantity > 1:
            cart[str(product_id)] = current_quantity - 1
        else:
            return False
        
        session['cart'] = cart
        session.modified = True
        return True
    
    @staticmethod
    def get_cart_items():
        """
        Récupère les items du panier avec leurs détails
        
        Returns:
            tuple: (cart_items: list, total: float)
        """
        from sqlalchemy.orm import joinedload
        
        cart = CartService.get_cart()
        cart_items = []
        total = 0
        
        if not cart:
            return cart_items, total
        
        # Récupérer tous les produits en une seule requête avec eager loading
        product_ids = [int(pid) for pid in cart.keys()]
        products = Product.query.options(
            joinedload(Product.category)
        ).filter(Product.id.in_(product_ids)).all()
        
        # Créer un dictionnaire pour accès rapide
        products_dict = {p.id: p for p in products}
        
        # Construire les items du panier
        for product_id, quantity in cart.items():
            product = products_dict.get(int(product_id))
            if product:
                subtotal = product.price * quantity
                total += subtotal
                cart_items.append({
                    'product': product,
                    'quantity': quantity,
                    'subtotal': subtotal
                })
        
        return cart_items, total
    
    @staticmethod
    def get_total_items():
        """
        Récupère le nombre total d'items dans le panier
        
        Returns:
            int: Nombre total d'items
        """
        cart = CartService.get_cart()
        return sum(cart.values())
    
    @staticmethod
    def clear_cart():
        """Vide le panier"""
        session['cart'] = {}
        session.modified = True
    
    @staticmethod
    def validate_cart():
        """
        Valide que tous les produits du panier sont disponibles
        
        Returns:
            tuple: (valid: bool, error_message: str or None)
        """
        cart = CartService.get_cart()
        
        if not cart:
            return False, 'Votre panier est vide'
        
        for product_id, quantity in cart.items():
            product = Product.query.get(int(product_id))
            if not product:
                return False, f'Produit {product_id} introuvable'
            if product.stock < quantity:
                return False, f'Stock insuffisant pour {product.name}'
        
        return True, None
