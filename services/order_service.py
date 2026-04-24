"""
Service de gestion des commandes
"""
from models.order import Order, OrderItem
from models.product import Product
from extensions import db
from .cart_service import CartService


class OrderService:
    """Service pour gérer les commandes"""
    
    @staticmethod
    def create_order_from_cart(user_id):
        """
        Crée une commande à partir du panier
        
        Args:
            user_id: ID de l'utilisateur
            
        Returns:
            tuple: (success: bool, message: str, order: Order or None)
        """
        # Valider le panier
        valid, error_message = CartService.validate_cart()
        if not valid:
            return False, error_message, None
        
        cart = CartService.get_cart()
        total = 0
        order_items = []
        
        # Préparer les items de commande
        for product_id, quantity in cart.items():
            product = Product.query.get(int(product_id))
            
            if not product or product.stock < quantity:
                return False, f'Stock insuffisant pour {product.name if product else "produit inconnu"}', None
            
            subtotal = product.price * quantity
            total += subtotal
            
            # Mettre à jour le stock
            product.stock -= quantity
            
            # Créer l'item de commande
            order_item = OrderItem(
                product_id=product.id,
                quantity=quantity,
                price=product.price
            )
            order_items.append(order_item)
        
        # Créer la commande
        order = Order(
            user_id=user_id,
            total_price=total,
            status='En attente'
        )
        
        # Ajouter les items à la commande
        for item in order_items:
            order.order_items.append(item)
        
        try:
            db.session.add(order)
            db.session.commit()
            
            # Vider le panier
            CartService.clear_cart()
            
            return True, 'Commande effectuée avec succès', order
        except Exception as e:
            db.session.rollback()
            return False, f'Erreur lors de la création de la commande: {str(e)}', None
    
    @staticmethod
    def get_order_by_id(order_id):
        """
        Récupère une commande par son ID
        
        Args:
            order_id: ID de la commande
            
        Returns:
            Order or None: La commande ou None
        """
        return Order.query.get(order_id)
    
    @staticmethod
    def get_user_orders(user_id):
        """
        Récupère toutes les commandes d'un utilisateur
        
        Args:
            user_id: ID de l'utilisateur
            
        Returns:
            list: Liste des commandes
        """
        return Order.query.filter_by(user_id=user_id).order_by(Order.created_at.desc()).all()
    
    @staticmethod
    def update_order_status(order_id, new_status):
        """
        Met à jour le statut d'une commande
        
        Args:
            order_id: ID de la commande
            new_status: Nouveau statut
            
        Returns:
            tuple: (success: bool, message: str, order: Order or None)
        """
        order = Order.query.get(order_id)
        
        if not order:
            return False, 'Commande introuvable', None
        
        order.status = new_status
        
        try:
            db.session.commit()
            return True, 'Statut mis à jour', order
        except Exception as e:
            db.session.rollback()
            return False, f'Erreur lors de la mise à jour: {str(e)}', None
    
    @staticmethod
    def cancel_order(order_id):
        """
        Annule une commande et restaure le stock
        
        Args:
            order_id: ID de la commande
            
        Returns:
            tuple: (success: bool, message: str)
        """
        order = Order.query.get(order_id)
        
        if not order:
            return False, 'Commande introuvable'
        
        if order.status not in ['En attente', 'En cours']:
            return False, 'Cette commande ne peut pas être annulée'
        
        # Restaurer le stock
        for item in order.order_items:
            product = Product.query.get(item.product_id)
            if product:
                product.stock += item.quantity
        
        order.status = 'Annulée'
        
        try:
            db.session.commit()
            return True, 'Commande annulée avec succès'
        except Exception as e:
            db.session.rollback()
            return False, f'Erreur lors de l\'annulation: {str(e)}'
    
    @staticmethod
    def get_all_orders(status=None):
        """
        Récupère toutes les commandes (pour admin)
        
        Args:
            status: Filtrer par statut (optionnel)
            
        Returns:
            list: Liste des commandes
        """
        query = Order.query
        
        if status:
            query = query.filter_by(status=status)
        
        return query.order_by(Order.created_at.desc()).all()
