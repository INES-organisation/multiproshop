"""
Intégration eBay API
Documentation: https://developer.ebay.com/
"""
from .base_provider import BaseApiProvider
from typing import List, Dict, Optional
import base64

class EbayProvider(BaseApiProvider):
    """Provider pour eBay API (Affiliation)"""
    
    def __init__(self, api_provider):
        super().__init__(api_provider)
        # eBay utilise Client ID et Client Secret pour OAuth
        self.client_id = api_provider.api_key
        self.client_secret = api_provider.api_secret
        self.campaign_id = api_provider.config.get('campaign_id', '') if api_provider.config else ''
        self.marketplace_id = api_provider.config.get('marketplace_id', 'EBAY_FR') if api_provider.config else 'EBAY_FR'
        self.access_token = None
    
    def _setup_session(self):
        """Configurer la session avec authentification eBay"""
        super()._setup_session()
        # Obtenir le token OAuth
        self._get_access_token()
    
    def _get_access_token(self):
        """Obtenir un token d'accès OAuth 2.0"""
        try:
            # Encoder les credentials en Base64
            credentials = f"{self.client_id}:{self.client_secret}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            
            # Requête OAuth
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Authorization': f'Basic {encoded_credentials}'
            }
            
            data = {
                'grant_type': 'client_credentials',
                'scope': 'https://api.ebay.com/oauth/api_scope'
            }
            
            response = self.session.post(
                'https://api.ebay.com/identity/v1/oauth2/token',
                headers=headers,
                data=data
            )
            
            if response.status_code == 200:
                self.access_token = response.json().get('access_token')
                self.session.headers.update({
                    'Authorization': f'Bearer {self.access_token}',
                    'X-EBAY-C-MARKETPLACE-ID': self.marketplace_id
                })
        except Exception as e:
            print(f"Erreur OAuth eBay: {e}")
    
    def test_connection(self) -> bool:
        """Tester la connexion à eBay"""
        try:
            if not self.access_token:
                self._get_access_token()
            
            # Test avec une recherche simple
            response = self.session.get(
                f'{self.api_endpoint}/buy/browse/v1/item_summary/search',
                params={'q': 'test', 'limit': 1}
            )
            return response.status_code == 200
        except:
            return False
    
    def get_categories(self) -> List[Dict]:
        """Récupérer les catégories eBay"""
        try:
            response = self.session.get(
                f'{self.api_endpoint}/commerce/taxonomy/v1/category_tree/{self._get_category_tree_id()}'
            )
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_ebay_categories(data.get('rootCategoryNode', {}))
            
            return []
        except Exception as e:
            print(f"Erreur récupération catégories eBay: {e}")
            return []
    
    def _get_category_tree_id(self) -> str:
        """Obtenir l'ID de l'arbre de catégories selon le marketplace"""
        mapping = {
            'EBAY_US': '0',
            'EBAY_GB': '3',
            'EBAY_FR': '71',
            'EBAY_DE': '77',
            'EBAY_IT': '101',
            'EBAY_ES': '186'
        }
        return mapping.get(self.marketplace_id, '71')
    
    def _parse_ebay_categories(self, node: Dict, parent_id: Optional[str] = None) -> List[Dict]:
        """Parser récursivement les catégories eBay"""
        categories = []
        
        if 'category' in node:
            cat = node['category']
            categories.append({
                'id': cat.get('categoryId'),
                'name': cat.get('categoryName'),
                'parent_id': parent_id,
                'level': node.get('categoryTreeNodeLevel', 0)
            })
            
            # Parser les sous-catégories
            for child in node.get('childCategoryTreeNodes', []):
                categories.extend(self._parse_ebay_categories(child, cat.get('categoryId')))
        
        return categories
    
    def get_products(self, category_id: Optional[str] = None, page: int = 1, limit: int = 50) -> Dict:
        """Récupérer les produits eBay"""
        try:
            params = {
                'limit': min(limit, 200),  # eBay max 200
                'offset': (page - 1) * limit
            }
            
            if category_id:
                params['category_ids'] = category_id
            else:
                params['q'] = 'popular'
            
            # Ajouter le filtre pour les articles neufs
            params['filter'] = 'conditionIds:{1000}'  # 1000 = Neuf
            
            response = self.session.get(
                f'{self.api_endpoint}/buy/browse/v1/item_summary/search',
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                
                products = []
                for item in data.get('itemSummaries', []):
                    products.append(self._format_product(item))
                
                total = data.get('total', 0)
                
                return {
                    'products': products,
                    'pagination': {
                        'page': page,
                        'limit': limit,
                        'total': total,
                        'pages': (total + limit - 1) // limit
                    }
                }
            
            return {'products': [], 'pagination': {}}
            
        except Exception as e:
            print(f"Erreur récupération produits eBay: {e}")
            return {'products': [], 'pagination': {}}
    
    def get_product_details(self, product_id: str) -> Dict:
        """Récupérer les détails d'un produit eBay"""
        try:
            response = self.session.get(
                f'{self.api_endpoint}/buy/browse/v1/item/{product_id}'
            )
            
            if response.status_code == 200:
                return self._format_product(response.json())
            
            return {}
        except Exception as e:
            print(f"Erreur détails produit eBay: {e}")
            return {}
    
    def get_product_stock(self, product_id: str, variant_id: Optional[str] = None) -> int:
        """Récupérer le stock d'un produit eBay"""
        try:
            response = self.session.get(
                f'{self.api_endpoint}/buy/browse/v1/item/{product_id}'
            )
            
            if response.status_code == 200:
                data = response.json()
                # eBay retourne estimatedAvailableQuantity
                return data.get('estimatedAvailabilities', [{}])[0].get('estimatedAvailableQuantity', 0)
            
            return 0
        except Exception as e:
            print(f"Erreur stock produit eBay: {e}")
            return 0
    
    def create_order(self, order_data: Dict) -> Dict:
        """
        eBay API ne permet pas de créer des commandes directement
        C'est un système d'affiliation : redirection vers eBay
        """
        return {
            'success': False,
            'error': 'eBay est un système d\'affiliation. Les clients achètent directement sur eBay.',
            'affiliate_link': self._generate_affiliate_link(order_data.get('items', []))
        }
    
    def get_order_status(self, order_id: str) -> Dict:
        """eBay API affiliation ne permet pas de suivre les commandes"""
        return {
            'error': 'Suivi de commande non disponible avec eBay Partner Network (affiliation)'
        }
    
    def _generate_affiliate_link(self, items: List[Dict]) -> str:
        """Générer un lien affilié eBay"""
        if not items or not self.campaign_id:
            return 'https://www.ebay.fr'
        
        item_id = items[0].get('external_product_id', '')
        # Lien eBay Partner Network
        return f'https://rover.ebay.com/rover/1/709-53476-19255-0/1?campid={self.campaign_id}&toolid=10001&mpre=https://www.ebay.fr/itm/{item_id}'
    
    def _format_product(self, raw_data: Dict) -> Dict:
        """Formater un produit eBay en format MPS"""
        price_data = raw_data.get('price', {})
        image = raw_data.get('image', {})
        
        return {
            'external_id': raw_data.get('itemId') or raw_data.get('legacyItemId'),
            'name': raw_data.get('title', ''),
            'description': raw_data.get('shortDescription', ''),
            'price': float(price_data.get('value', 0)),
            'compare_price': 0,
            'currency': price_data.get('currency', 'EUR'),
            'stock': raw_data.get('estimatedAvailabilities', [{}])[0].get('estimatedAvailableQuantity', 999),
            'sku': raw_data.get('itemId'),
            'images': [image.get('imageUrl', '')] if image else [],
            'category_id': raw_data.get('categoryId', ''),
            'category_name': raw_data.get('categoryPath', ''),
            'affiliate_link': self._generate_affiliate_link([{'external_product_id': raw_data.get('itemId')}]),
            'condition': raw_data.get('condition', 'New'),
            'seller': raw_data.get('seller', {}).get('username', ''),
            'raw_data': raw_data
        }
    
    def translate_product_data(self, raw_data: Dict) -> Dict:
        """Traduire les données eBay en format MPS"""
        return self._format_product(raw_data)
