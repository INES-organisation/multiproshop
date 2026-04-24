"""
Intégration Printify API
Documentation: https://developers.printify.com/
"""
from .base_provider import BaseApiProvider
from typing import List, Dict, Optional

class PrintifyProvider(BaseApiProvider):
    """Provider pour Printify (Print on Demand)"""
    
    def _setup_session(self):
        """Configurer la session avec authentification Printify"""
        super()._setup_session()
        
        # Printify utilise Bearer token
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}'
        })
    
    def test_connection(self) -> bool:
        """Tester la connexion à Printify"""
        try:
            response = self._make_request('GET', 'shops.json')
            return 'id' in response[0] if response else False
        except:
            return False
    
    def get_categories(self) -> List[Dict]:
        """Printify n'a pas de catégories, retourner les blueprints"""
        try:
            response = self._make_request('GET', 'catalog/blueprints.json')
            
            categories = []
            for blueprint in response:
                categories.append({
                    'id': str(blueprint.get('id')),
                    'name': blueprint.get('title'),
                    'description': blueprint.get('description'),
                    'type': 'blueprint'
                })
            return categories
        except Exception as e:
            print(f"Erreur récupération blueprints Printify: {e}")
            return []
    
    def get_products(self, category_id: Optional[str] = None, page: int = 1, limit: int = 50) -> Dict:
        """Récupérer les produits Printify"""
        try:
            # Récupérer le shop_id
            shops = self._make_request('GET', 'shops.json')
            if not shops:
                return {'products': [], 'pagination': {}}
            
            shop_id = shops[0]['id']
            
            params = {
                'page': page,
                'limit': min(limit, 100)
            }
            
            response = self._make_request('GET', f'shops/{shop_id}/products.json', params=params)
            
            products = []
            for item in response.get('data', []):
                products.append(self._format_product(item))
            
            return {
                'products': products,
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total': response.get('total', 0),
                    'pages': response.get('last_page', 1)
                }
            }
        except Exception as e:
            print(f"Erreur récupération produits Printify: {e}")
            return {'products': [], 'pagination': {}}
    
    def get_product_details(self, product_id: str) -> Dict:
        """Récupérer les détails d'un produit Printify"""
        try:
            shops = self._make_request('GET', 'shops.json')
            if not shops:
                return {}
            
            shop_id = shops[0]['id']
            response = self._make_request('GET', f'shops/{shop_id}/products/{product_id}.json')
            
            return self._format_product(response)
        except Exception as e:
            print(f"Erreur détails produit Printify: {e}")
            return {}
    
    def get_product_stock(self, product_id: str, variant_id: Optional[str] = None) -> int:
        """Printify = POD, stock illimité"""
        return 9999  # Stock virtuel pour Print on Demand
    
    def create_order(self, order_data: Dict) -> Dict:
        """Créer une commande chez Printify"""
        try:
            shops = self._make_request('GET', 'shops.json')
            if not shops:
                return {'success': False, 'error': 'No shop found'}
            
            shop_id = shops[0]['id']
            
            # Formater pour Printify
            printify_order = {
                'external_id': order_data.get('order_number'),
                'label': order_data.get('order_number'),
                'line_items': [],
                'shipping_method': 1,  # Standard
                'address_to': {
                    'first_name': order_data.get('shipping_first_name'),
                    'last_name': order_data.get('shipping_last_name'),
                    'email': order_data.get('customer_email'),
                    'phone': order_data.get('customer_phone'),
                    'country': order_data.get('shipping_country'),
                    'region': '',
                    'address1': order_data.get('shipping_address'),
                    'address2': '',
                    'city': order_data.get('shipping_city'),
                    'zip': order_data.get('shipping_postal_code')
                }
            }
            
            # Ajouter les produits
            for item in order_data.get('items', []):
                printify_order['line_items'].append({
                    'product_id': item.get('external_product_id'),
                    'variant_id': item.get('external_variant_id'),
                    'quantity': item.get('quantity')
                })
            
            response = self._make_request('POST', f'shops/{shop_id}/orders.json', json=printify_order)
            
            return {
                'success': True,
                'order_id': response.get('id'),
                'status': response.get('status')
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_order_status(self, order_id: str) -> Dict:
        """Récupérer le statut d'une commande Printify"""
        try:
            shops = self._make_request('GET', 'shops.json')
            if not shops:
                return {}
            
            shop_id = shops[0]['id']
            response = self._make_request('GET', f'shops/{shop_id}/orders/{order_id}.json')
            
            return {
                'order_id': response.get('id'),
                'status': response.get('status'),
                'tracking_number': response.get('shipments', [{}])[0].get('tracking_number'),
                'carrier': response.get('shipments', [{}])[0].get('carrier')
            }
        except Exception as e:
            print(f"Erreur statut commande Printify: {e}")
            return {}
    
    def _format_product(self, raw_data: Dict) -> Dict:
        """Formater un produit Printify en format MPS"""
        # Récupérer la première image
        images = []
        for img in raw_data.get('images', []):
            images.append(img.get('src'))
        
        return {
            'external_id': raw_data.get('id'),
            'name': raw_data.get('title'),
            'description': raw_data.get('description', ''),
            'price': 0,  # Prix calculé par variant
            'compare_price': 0,
            'currency': 'USD',
            'stock': 9999,  # POD = stock illimité
            'sku': '',
            'images': images,
            'category_id': str(raw_data.get('blueprint_id')),
            'category_name': 'Print on Demand',
            'variants': self._format_variants(raw_data.get('variants', [])),
            'raw_data': raw_data
        }
    
    def _format_variants(self, variants: List[Dict]) -> List[Dict]:
        """Formater les variants Printify"""
        formatted = []
        for variant in variants:
            formatted.append({
                'id': str(variant.get('id')),
                'sku': variant.get('sku'),
                'price': float(variant.get('price', 0)) / 100,  # Printify en centimes
                'stock': 9999,
                'attributes': variant.get('title')
            })
        return formatted
    
    def translate_product_data(self, raw_data: Dict) -> Dict:
        """Traduire les données Printify en format MPS"""
        return self._format_product(raw_data)
