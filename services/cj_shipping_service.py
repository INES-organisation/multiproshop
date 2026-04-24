"""
Service de gestion de la livraison CJ Dropshipping
Phase 1.2 - Checkout & Livraison
"""
import logging

logger = logging.getLogger(__name__)


class CjShippingService:
    """Service pour gérer la livraison CJ"""
    
    def __init__(self, cj_api):
        self.cj_api = cj_api
    
    def get_shipping_methods(self, country_code, product_ids=None):
        """
        Récupérer les méthodes de livraison disponibles pour un pays
        
        Args:
            country_code: Code pays ISO (ex: 'US', 'FR', 'CA')
            product_ids: Liste des IDs produits CJ (optionnel)
            
        Returns:
            dict: Méthodes de livraison disponibles
        """
        try:
            # Appel API CJ pour obtenir les méthodes de livraison
            # Endpoint: /shopping/logistics/query
            
            params = {
                'countryCode': country_code
            }
            
            if product_ids:
                params['productIds'] = ','.join(str(pid) for pid in product_ids)
            
            response = self.cj_api._make_request('POST', '/shopping/logistics/query', params)
            
            if not response or not response.get('data'):
                return {
                    'success': False,
                    'message': 'Aucune méthode de livraison disponible',
                    'methods': []
                }
            
            methods = []
            for method in response.get('data', []):
                methods.append({
                    'id': method.get('logisticsId'),
                    'name': method.get('logisticsName'),
                    'name_en': method.get('logisticsNameEn'),
                    'price': float(method.get('logisticsPrice', 0)),
                    'delivery_time': method.get('deliveryTime'),
                    'delivery_time_desc': method.get('deliveryTimeDesc'),
                    'tracking_available': method.get('trackingAvailable', True),
                    'description': method.get('description', '')
                })
            
            return {
                'success': True,
                'country_code': country_code,
                'methods': methods,
                'total_methods': len(methods)
            }
            
        except Exception as e:
            logger.error(f"Erreur get_shipping_methods: {e}")
            return {
                'success': False,
                'message': str(e),
                'methods': []
            }
    
    def calculate_shipping_cost(self, cart_items, country_code, shipping_method_id=None):
        """
        Calculer les frais de livraison pour un panier
        
        Args:
            cart_items: Liste des items du panier [{product_id, variant_id, quantity}]
            country_code: Code pays de destination
            shipping_method_id: ID méthode de livraison (optionnel)
            
        Returns:
            dict: Coût de livraison et détails
        """
        try:
            from models.product import Product
            from models.product_variant import ProductVariant
            
            # Préparer les données pour l'API CJ
            products_data = []
            total_weight = 0
            
            for item in cart_items:
                product = Product.query.get(item['product_id'])
                
                if not product or not product.cj_pid:
                    continue
                
                # Si variante spécifiée, utiliser ses données
                if item.get('variant_id'):
                    variant = ProductVariant.query.get(item['variant_id'])
                    if variant:
                        weight = variant.weight or 100
                        cj_vid = variant.cj_vid
                    else:
                        weight = 100
                        cj_vid = None
                else:
                    weight = 100  # Poids par défaut
                    cj_vid = None
                
                quantity = item.get('quantity', 1)
                total_weight += weight * quantity
                
                products_data.append({
                    'pid': product.cj_pid,
                    'vid': cj_vid,
                    'quantity': quantity,
                    'weight': weight
                })
            
            if not products_data:
                return {
                    'success': False,
                    'message': 'Aucun produit CJ dans le panier',
                    'shipping_cost': 0
                }
            
            # Appel API CJ pour calculer les frais
            # Endpoint: /shopping/logistics/freightCalculate
            
            params = {
                'countryCode': country_code,
                'products': products_data,
                'totalWeight': total_weight
            }
            
            if shipping_method_id:
                params['logisticsId'] = shipping_method_id
            
            response = self.cj_api._make_request('POST', '/shopping/logistics/freightCalculate', params)
            
            if not response or not response.get('data'):
                # Calcul par défaut si API échoue
                default_cost = self._calculate_default_shipping(total_weight, country_code)
                
                return {
                    'success': True,
                    'shipping_cost': default_cost,
                    'currency': 'USD',
                    'delivery_time': '15-30 jours',
                    'method': 'Standard',
                    'is_default': True,
                    'total_weight': total_weight
                }
            
            data = response.get('data', {})
            
            return {
                'success': True,
                'shipping_cost': float(data.get('freight', 0)),
                'currency': data.get('currency', 'USD'),
                'delivery_time': data.get('deliveryTime', '15-30 jours'),
                'method': data.get('logisticsName', 'Standard'),
                'method_id': data.get('logisticsId'),
                'tracking_available': data.get('trackingAvailable', True),
                'total_weight': total_weight,
                'is_default': False
            }
            
        except Exception as e:
            logger.error(f"Erreur calculate_shipping_cost: {e}")
            
            # Retourner un coût par défaut en cas d'erreur
            default_cost = 5.99
            
            return {
                'success': True,
                'shipping_cost': default_cost,
                'currency': 'USD',
                'delivery_time': '15-30 jours',
                'method': 'Standard',
                'is_default': True,
                'error': str(e)
            }
    
    def _calculate_default_shipping(self, weight_grams, country_code):
        """
        Calculer les frais de livraison par défaut basés sur le poids
        
        Args:
            weight_grams: Poids total en grammes
            country_code: Code pays
            
        Returns:
            float: Coût de livraison
        """
        # Tarifs par défaut basés sur le poids
        weight_kg = weight_grams / 1000
        
        # Tarif de base
        base_cost = 3.99
        
        # Coût par kg supplémentaire
        if weight_kg <= 0.5:
            cost = base_cost
        elif weight_kg <= 1:
            cost = base_cost + 2.00
        elif weight_kg <= 2:
            cost = base_cost + 4.00
        else:
            cost = base_cost + 4.00 + ((weight_kg - 2) * 1.50)
        
        # Majoration selon le pays
        zone_multipliers = {
            'US': 1.0,
            'CA': 1.1,
            'GB': 1.2,
            'FR': 1.2,
            'DE': 1.2,
            'ES': 1.2,
            'IT': 1.2,
            'AU': 1.5,
            'JP': 1.4,
            'CN': 1.0,
        }
        
        multiplier = zone_multipliers.get(country_code, 1.3)
        final_cost = cost * multiplier
        
        return round(final_cost, 2)
    
    def estimate_delivery_time(self, country_code, shipping_method_id=None):
        """
        Estimer le délai de livraison
        
        Args:
            country_code: Code pays
            shipping_method_id: ID méthode de livraison
            
        Returns:
            dict: Estimation du délai
        """
        try:
            # Délais par défaut selon les zones
            delivery_times = {
                'US': {'min': 7, 'max': 15, 'desc': '7-15 jours ouvrés'},
                'CA': {'min': 10, 'max': 20, 'desc': '10-20 jours ouvrés'},
                'GB': {'min': 10, 'max': 20, 'desc': '10-20 jours ouvrés'},
                'FR': {'min': 12, 'max': 25, 'desc': '12-25 jours ouvrés'},
                'DE': {'min': 12, 'max': 25, 'desc': '12-25 jours ouvrés'},
                'ES': {'min': 15, 'max': 30, 'desc': '15-30 jours ouvrés'},
                'IT': {'min': 15, 'max': 30, 'desc': '15-30 jours ouvrés'},
                'AU': {'min': 15, 'max': 35, 'desc': '15-35 jours ouvrés'},
                'JP': {'min': 10, 'max': 20, 'desc': '10-20 jours ouvrés'},
            }
            
            default = {'min': 15, 'max': 30, 'desc': '15-30 jours ouvrés'}
            
            time_info = delivery_times.get(country_code, default)
            
            return {
                'success': True,
                'country_code': country_code,
                'min_days': time_info['min'],
                'max_days': time_info['max'],
                'description': time_info['desc'],
                'estimated_date_min': None,  # À calculer avec datetime
                'estimated_date_max': None
            }
            
        except Exception as e:
            logger.error(f"Erreur estimate_delivery_time: {e}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def validate_shipping_address(self, address_data):
        """
        Valider une adresse de livraison
        
        Args:
            address_data: Données de l'adresse
            
        Returns:
            dict: Résultat de la validation
        """
        try:
            required_fields = ['country', 'city', 'address', 'zip_code']
            missing_fields = []
            
            for field in required_fields:
                if not address_data.get(field):
                    missing_fields.append(field)
            
            if missing_fields:
                return {
                    'success': False,
                    'valid': False,
                    'message': f'Champs manquants: {", ".join(missing_fields)}',
                    'missing_fields': missing_fields
                }
            
            # Vérifier si le pays est supporté par CJ
            supported_countries = self.get_supported_countries()
            
            country_code = address_data.get('country')
            
            if country_code not in supported_countries:
                return {
                    'success': False,
                    'valid': False,
                    'message': f'Pays non supporté: {country_code}',
                    'supported_countries': supported_countries
                }
            
            return {
                'success': True,
                'valid': True,
                'message': 'Adresse valide',
                'normalized_address': address_data
            }
            
        except Exception as e:
            logger.error(f"Erreur validate_shipping_address: {e}")
            return {
                'success': False,
                'valid': False,
                'message': str(e)
            }
    
    def get_supported_countries(self):
        """
        Obtenir la liste des pays supportés par CJ
        
        Returns:
            list: Codes pays ISO
        """
        # Liste des principaux pays supportés par CJ
        return [
            'US', 'CA', 'GB', 'FR', 'DE', 'ES', 'IT', 'NL', 'BE', 'AT',
            'CH', 'SE', 'NO', 'DK', 'FI', 'IE', 'PT', 'GR', 'PL', 'CZ',
            'AU', 'NZ', 'JP', 'KR', 'SG', 'MY', 'TH', 'VN', 'PH', 'ID',
            'IN', 'AE', 'SA', 'IL', 'ZA', 'BR', 'MX', 'AR', 'CL', 'CO'
        ]
    
    def get_shipping_zones(self):
        """
        Obtenir les zones de livraison avec tarifs indicatifs
        
        Returns:
            dict: Zones de livraison
        """
        return {
            'zone_1': {
                'name': 'Amérique du Nord',
                'countries': ['US', 'CA'],
                'base_cost': 5.99,
                'delivery_time': '7-15 jours'
            },
            'zone_2': {
                'name': 'Europe Occidentale',
                'countries': ['GB', 'FR', 'DE', 'ES', 'IT', 'NL', 'BE'],
                'base_cost': 7.99,
                'delivery_time': '12-25 jours'
            },
            'zone_3': {
                'name': 'Europe du Nord',
                'countries': ['SE', 'NO', 'DK', 'FI'],
                'base_cost': 8.99,
                'delivery_time': '15-30 jours'
            },
            'zone_4': {
                'name': 'Océanie',
                'countries': ['AU', 'NZ'],
                'base_cost': 9.99,
                'delivery_time': '15-35 jours'
            },
            'zone_5': {
                'name': 'Asie',
                'countries': ['JP', 'KR', 'SG', 'MY', 'TH'],
                'base_cost': 6.99,
                'delivery_time': '10-20 jours'
            },
            'zone_6': {
                'name': 'Reste du monde',
                'countries': [],
                'base_cost': 12.99,
                'delivery_time': '20-40 jours'
            }
        }
