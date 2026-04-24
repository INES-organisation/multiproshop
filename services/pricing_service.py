"""
Service de gestion de la tarification et des marges
Calcule automatiquement les prix de vente depuis les prix CJ
"""
from extensions import db
from models.product import Product
from models.category import Category
import math


class PricingService:
    """Service de calcul des prix et gestion des marges"""
    
    def __init__(self):
        self.default_markup = 60.0  # Marge par défaut : 60%
        
        # Marges par catégorie (à configurer)
        self.category_markups = {
            'Electronics': 50.0,
            'Fashion': 80.0,
            'Home & Garden': 70.0,
            'Jewelry': 100.0,
            'Toys': 60.0,
            'Computer & Office': 50.0,
            'Consumer Electronics': 50.0,
            'Automobiles & Motorcycles': 55.0,
            'Women\'s Clothing': 80.0,
            'Men\'s Clothing': 80.0,
            'Pet Supplies': 65.0,
            'Health, Beauty & Hair': 75.0,
            'Jewelry & Watches': 100.0,
            'Bags & Shoes': 85.0,
            'Toys, Kids & Babies': 60.0,
            'Sports & Outdoors': 65.0,
            'Home, Garden & Furniture': 70.0,
        }
    
    def get_markup_for_category(self, category_name):
        """
        Récupère la marge applicable pour une catégorie
        
        Args:
            category_name (str): Nom de la catégorie
            
        Returns:
            float: Pourcentage de marge
        """
        if not category_name:
            return self.default_markup
        
        # Chercher une correspondance exacte
        if category_name in self.category_markups:
            return self.category_markups[category_name]
        
        # Chercher une correspondance partielle
        for cat_key, markup in self.category_markups.items():
            if cat_key.lower() in category_name.lower() or category_name.lower() in cat_key.lower():
                return markup
        
        return self.default_markup
    
    def get_markup_for_product(self, product):
        """
        Récupère la marge applicable pour un produit
        
        Args:
            product (Product): Instance du produit
            
        Returns:
            float: Pourcentage de marge
        """
        if not product.category_id:
            return self.default_markup
        
        category = Category.query.get(product.category_id)
        if not category:
            return self.default_markup
        
        return self.get_markup_for_category(category.name)
    
    def calculate_selling_price(self, cost_price, markup_percentage, rounding='nearest_99'):
        """
        Calcule le prix de vente avec marge et arrondi
        
        Args:
            cost_price (float): Prix de revient (prix CJ)
            markup_percentage (float): Pourcentage de marge
            rounding (str): Stratégie d'arrondi ('nearest_99', 'up', 'down', 'none')
            
        Returns:
            float: Prix de vente calculé
        """
        if not cost_price or cost_price <= 0:
            return 0.0
        
        if not markup_percentage or markup_percentage < 0:
            markup_percentage = self.default_markup
        
        # Calcul de base
        price = cost_price * (1 + markup_percentage / 100)
        
        # Stratégie d'arrondi
        if rounding == 'nearest_99':
            # Arrondi psychologique à .99
            if price >= 10:
                price = math.floor(price) + 0.99
            else:
                price = round(price, 2)
        elif rounding == 'up':
            price = math.ceil(price)
        elif rounding == 'down':
            price = math.floor(price)
        else:
            price = round(price, 2)
        
        return round(price, 2)
    
    def calculate_profit(self, selling_price, cost_price):
        """
        Calcule le bénéfice par vente
        
        Args:
            selling_price (float): Prix de vente
            cost_price (float): Prix de revient
            
        Returns:
            float: Bénéfice
        """
        if not selling_price or not cost_price:
            return 0.0
        
        return round(selling_price - cost_price, 2)
    
    def calculate_margin_percentage(self, selling_price, cost_price):
        """
        Calcule la marge en pourcentage (marge commerciale sur prix de vente)
        
        Args:
            selling_price (float): Prix de vente
            cost_price (float): Prix de revient
            
        Returns:
            float: Marge en %
        """
        profit = self.calculate_profit(selling_price, cost_price)
        
        if profit <= 0 or not selling_price or selling_price <= 0:
            return 0.0
        
        return round((profit / selling_price) * 100, 2)
    
    def calculate_markup_percentage(self, selling_price, cost_price):
        """
        Calcule le markup (majoration) en pourcentage appliqué au coût
        C'est la marge configurée qui a été appliquée
        
        Args:
            selling_price (float): Prix de vente
            cost_price (float): Prix de revient
            
        Returns:
            float: Markup en %
        """
        if not cost_price or cost_price <= 0:
            return 0.0
        
        if not selling_price or selling_price <= 0:
            return 0.0
        
        profit = selling_price - cost_price
        return round((profit / cost_price) * 100, 2)
    
    def update_product_pricing(self, product, cj_sell_price, cj_suggested_price=None):
        """
        Met à jour les prix d'un produit depuis les données CJ
        
        Args:
            product (Product): Instance du produit
            cj_sell_price (float): Prix CJ (sellPrice)
            cj_suggested_price (float): Prix suggéré CJ (suggestSellPrice)
            
        Returns:
            Product: Produit mis à jour
        """
        # Récupérer la marge applicable
        markup = self.get_markup_for_product(product)
        
        # Calculer le prix de vente
        selling_price = self.calculate_selling_price(cj_sell_price, markup)
        
        # Mettre à jour les prix
        product.cost_price = cj_sell_price
        product.price = selling_price
        
        if cj_suggested_price:
            product.compare_price = cj_suggested_price
            product.suggested_price = cj_suggested_price
        
        return product
    
    def recalculate_all_prices(self, category_id=None):
        """
        Recalcule les prix de tous les produits (ou d'une catégorie)
        
        Args:
            category_id (int): ID de la catégorie (None = tous les produits)
            
        Returns:
            dict: Résultat de l'opération
        """
        try:
            # Construire la requête
            query = Product.query.filter(
                Product.cj_pid.isnot(None),
                Product.cost_price.isnot(None),
                Product.cost_price > 0
            )
            
            if category_id:
                query = query.filter(Product.category_id == category_id)
            
            products = query.all()
            updated_count = 0
            
            for product in products:
                # Récupérer la marge
                markup = self.get_markup_for_product(product)
                
                # Calculer le nouveau prix
                new_price = self.calculate_selling_price(product.cost_price, markup)
                
                # Mettre à jour si différent
                if product.price != new_price:
                    product.price = new_price
                    updated_count += 1
            
            db.session.commit()
            
            return {
                'success': True,
                'total': len(products),
                'updated': updated_count,
                'message': f'{updated_count} produits mis à jour sur {len(products)}'
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Erreur: {str(e)}'
            }
    
    def get_pricing_analytics(self, category_id=None):
        """
        Récupère les analytics de tarification
        
        Args:
            category_id (int): ID de la catégorie (None = tous)
            
        Returns:
            dict: Analytics de tarification
        """
        try:
            # Construire la requête
            query = Product.query.filter(
                Product.cj_pid.isnot(None),
                Product.cost_price.isnot(None),
                Product.price.isnot(None)
            )
            
            if category_id:
                query = query.filter(Product.category_id == category_id)
            
            products = query.all()
            
            if not products:
                return {
                    'total_products': 0,
                    'avg_cost_price': 0,
                    'avg_selling_price': 0,
                    'avg_margin_percentage': 0,
                    'total_potential_profit': 0,
                    'products_by_margin_range': {
                        '0-30%': 0,
                        '30-50%': 0,
                        '50-70%': 0,
                        '70-100%': 0,
                        '100%+': 0
                    }
                }
            
            total_cost = sum(p.cost_price for p in products if p.cost_price)
            total_price = sum(p.price for p in products if p.price)
            total_margin = 0
            
            margin_ranges = {
                '0-30%': 0,
                '30-50%': 0,
                '50-70%': 0,
                '70-100%': 0,
                '100%+': 0
            }
            
            for product in products:
                if product.cost_price and product.price:
                    # Utiliser le markup (marge appliquée) au lieu de la marge commerciale
                    markup = self.calculate_markup_percentage(product.price, product.cost_price)
                    total_margin += markup
                    
                    # Classifier par tranche de markup
                    if markup < 30:
                        margin_ranges['0-30%'] += 1
                    elif markup < 50:
                        margin_ranges['30-50%'] += 1
                    elif markup < 70:
                        margin_ranges['50-70%'] += 1
                    elif markup < 100:
                        margin_ranges['70-100%'] += 1
                    else:
                        margin_ranges['100%+'] += 1
            
            return {
                'total_products': len(products),
                'avg_cost_price': round(total_cost / len(products), 2),
                'avg_selling_price': round(total_price / len(products), 2),
                'avg_margin_percentage': round(total_margin / len(products), 2),
                'total_potential_profit': round(total_price - total_cost, 2),
                'products_by_margin_range': margin_ranges
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'total_products': 0
            }
    
    def set_category_markup(self, category_name, markup_percentage):
        """
        Définit la marge pour une catégorie
        
        Args:
            category_name (str): Nom de la catégorie
            markup_percentage (float): Pourcentage de marge
        """
        self.category_markups[category_name] = markup_percentage
    
    def get_all_markups(self):
        """
        Récupère toutes les marges configurées
        
        Returns:
            dict: Dictionnaire des marges
        """
        return {
            'default': self.default_markup,
            'categories': self.category_markups
        }
