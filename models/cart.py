import json

from flask import session
from flask_login import current_user
from models.product import Product
from models.product_variant import ProductVariant

USD_TO_EUR = 0.92


def admin_cost_mode():
    """Un admin connecté achète au prix coûtant CJ (commandes de test ou pour son usage)"""
    try:
        return bool(current_user.is_authenticated and current_user.is_admin)
    except Exception:  # hors requête
        return False


def cost_price(product, variant=None):
    """Coût d'achat CJ en euros : celui de la variante si CJ le donne, sinon celui du produit"""
    if variant is not None and variant.cj_raw_data:
        try:
            raw = json.loads(variant.cj_raw_data)
            usd = float(raw.get('price') or raw.get('variantSellPrice') or 0)
        except (ValueError, TypeError, AttributeError):
            usd = 0
        if usd > 0:
            return round(usd * USD_TO_EUR, 2)
    return product.cost_price or None

class Cart:
    """Classe pour gérer le panier en session avec support des variantes"""
    
    def __init__(self):
        if 'cart' not in session:
            session['cart'] = {}

    def add_item(self, product_id, quantity=1, variant_id=None):
        """
        Ajouter un produit au panier avec variante optionnelle
        
        Args:
            product_id: ID du produit
            quantity: Quantité à ajouter
            variant_id: ID de la variante (optionnel)
        """
        cart = session['cart']
        
        # Créer une clé unique pour le produit + variante
        if variant_id:
            cart_key = f"{product_id}_v{variant_id}"
        else:
            cart_key = str(product_id)
        
        if cart_key in cart:
            cart[cart_key]['quantity'] += quantity
        else:
            cart[cart_key] = {
                'product_id': product_id,
                'variant_id': variant_id,
                'quantity': quantity
            }
        
        session['cart'] = cart
        session.modified = True
        return True

    def update_quantity(self, cart_key, quantity):
        """Mettre à jour la quantité d'un item (produit ou variante)"""
        cart = session['cart']
        
        if quantity <= 0:
            return self.remove_item(cart_key)
        
        if cart_key in cart:
            cart[cart_key]['quantity'] = quantity
            session['cart'] = cart
            session.modified = True
            return True
        return False

    def remove_item(self, cart_key):
        """Supprimer un item du panier"""
        cart = session['cart']
        
        if cart_key in cart:
            del cart[cart_key]
            session['cart'] = cart
            session.modified = True
            return True
        return False

    def get_items(self):
        """Récupérer les items du panier (dict simple)"""
        return session.get('cart', {})

    def get_items_with_products(self):
        """Récupérer les items avec les détails des produits et variantes"""
        cart = session.get('cart', {})
        items = []
        
        for cart_key, item_data in cart.items():
            # Support ancien format (migration)
            if isinstance(item_data, int):
                product_id = int(cart_key)
                quantity = item_data
                variant_id = None
            else:
                product_id = item_data['product_id']
                quantity = item_data['quantity']
                variant_id = item_data.get('variant_id')
            
            product = Product.query.get(product_id)
            if product:
                variant = None
                price = product.price
                
                # Si variante, utiliser son prix et ses infos
                if variant_id:
                    variant = ProductVariant.query.get(variant_id)
                    if variant and variant.price:
                        price = variant.price
                
                if admin_cost_mode():
                    price = cost_price(product, variant) or price

                items.append({
                    'cart_key': cart_key,
                    'product': product,
                    'variant': variant,
                    'quantity': quantity,
                    'price': price,
                    'subtotal': price * quantity
                })
        
        return items

    def clear(self):
        """Vider le panier"""
        session['cart'] = {}
        session.modified = True

    def get_total_items(self):
        """Nombre total d'articles dans le panier"""
        cart = session.get('cart', {})
        total = 0
        for item_data in cart.values():
            if isinstance(item_data, int):
                total += item_data
            else:
                total += item_data['quantity']
        return total

    def get_total_price(self):
        """Prix total du panier"""
        items = self.get_items_with_products()
        return sum(item['subtotal'] for item in items)

    def get_item_count(self):
        """Nombre de produits différents dans le panier"""
        return len(session.get('cart', {}))

    def has_item(self, product_id, variant_id=None):
        """Vérifier si un produit (avec variante optionnelle) est dans le panier"""
        if variant_id:
            cart_key = f"{product_id}_v{variant_id}"
        else:
            cart_key = str(product_id)
        return cart_key in session.get('cart', {})

    def get_item_quantity(self, product_id, variant_id=None):
        """Obtenir la quantité d'un produit (avec variante optionnelle) dans le panier"""
        if variant_id:
            cart_key = f"{product_id}_v{variant_id}"
        else:
            cart_key = str(product_id)
        
        cart = session.get('cart', {})
        item_data = cart.get(cart_key, 0)
        
        if isinstance(item_data, int):
            return item_data
        else:
            return item_data.get('quantity', 0)

    def is_empty(self):
        """Vérifier si le panier est vide"""
        return len(session.get('cart', {})) == 0

    def validate_stock(self):
        """Vérifier que tous les produits et variantes sont en stock"""
        items = self.get_items_with_products()
        errors = []
        
        for item in items:
            product = item['product']
            variant = item.get('variant')
            quantity = item['quantity']
            
            if not product.is_active:
                errors.append(f"{product.name} n'est plus disponible")
            elif variant:
                # Vérifier le stock de la variante
                if not variant.active:
                    errors.append(f"{product.name} ({variant.display_name}) n'est plus disponible")
                else:
                    # Même règle que l'ajout au panier et la fiche : sans stock connu pour la
                    # variante (CJ ne le donne pas toujours), celui du produit
                    stock = variant.stock if variant.stock > 0 else product.stock
                    if stock < quantity:
                        errors.append(f"{product.name} ({variant.display_name}): seulement {stock} en stock")
            else:
                # Vérifier le stock du produit
                if product.stock < quantity:
                    errors.append(f"{product.name}: seulement {product.stock} en stock")
        
        return errors
