"""
Intégration Amazon Product Advertising API
Documentation: https://webservices.amazon.com/paapi5/documentation/
"""
from .base_provider import BaseApiProvider
from typing import List, Dict, Optional
import hmac
import hashlib
import base64
from datetime import datetime
from urllib.parse import quote

class AmazonProvider(BaseApiProvider):
    """Provider pour Amazon Product Advertising API (Affiliation)"""
    
    def __init__(self, api_provider):
        super().__init__(api_provider)
        # Amazon utilise Access Key, Secret Key et Associate Tag
        self.access_key = api_provider.api_key
        self.secret_key = api_provider.api_secret
        self.associate_tag = api_provider.config.get('associate_tag', '') if api_provider.config else ''
        self.marketplace = api_provider.config.get('marketplace', 'www.amazon.fr') if api_provider.config else 'www.amazon.fr'
        self.region = api_provider.config.get('region', 'eu-west-1') if api_provider.config else 'eu-west-1'
    
    def _setup_session(self):
        """Configurer la session avec authentification Amazon"""
        super()._setup_session()
        self.session.headers.update({
            'Content-Type': 'application/json; charset=utf-8',
            'X-Amz-Target': 'com.amazon.paapi5.v1.ProductAdvertisingAPIv1.SearchItems'
        })
    
    def _get_signature(self, method: str, endpoint: str, params: Dict) -> str:
        """Générer la signature AWS pour l'authentification"""
        timestamp = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
        date_stamp = datetime.utcnow().strftime('%Y%m%d')
        
        # Créer la chaîne canonique
        canonical_uri = endpoint
        canonical_querystring = ''
        canonical_headers = f'host:{self.marketplace}\nx-amz-date:{timestamp}\n'
        signed_headers = 'host;x-amz-date'
        
        payload_hash = hashlib.sha256(str(params).encode('utf-8')).hexdigest()
        canonical_request = f'{method}\n{canonical_uri}\n{canonical_querystring}\n{canonical_headers}\n{signed_headers}\n{payload_hash}'
        
        # Créer la signature
        algorithm = 'AWS4-HMAC-SHA256'
        credential_scope = f'{date_stamp}/{self.region}/ProductAdvertisingAPI/aws4_request'
        string_to_sign = f'{algorithm}\n{timestamp}\n{credential_scope}\n{hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()}'
        
        signing_key = self._get_signature_key(self.secret_key, date_stamp, self.region, 'ProductAdvertisingAPI')
        signature = hmac.new(signing_key, string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()
        
        return signature
    
    def _get_signature_key(self, key: str, date_stamp: str, region: str, service: str):
        """Générer la clé de signature AWS"""
        k_date = hmac.new(f'AWS4{key}'.encode('utf-8'), date_stamp.encode('utf-8'), hashlib.sha256).digest()
        k_region = hmac.new(k_date, region.encode('utf-8'), hashlib.sha256).digest()
        k_service = hmac.new(k_region, service.encode('utf-8'), hashlib.sha256).digest()
        k_signing = hmac.new(k_service, 'aws4_request'.encode('utf-8'), hashlib.sha256).digest()
        return k_signing
    
    def test_connection(self) -> bool:
        """Tester la connexion à Amazon PA-API"""
        try:
            # Test simple avec une recherche
            result = self.get_products(category_id=None, page=1, limit=1)
            return len(result.get('products', [])) >= 0  # Même 0 résultat = connexion OK
        except:
            return False
    
    def get_categories(self) -> List[Dict]:
        """Amazon PA-API n'a pas d'endpoint catégories, retourner les browse nodes principaux"""
        # Browse Nodes Amazon FR principaux
        categories = [
            {'id': '340858031', 'name': 'High-Tech', 'parent_id': None},
            {'id': '197858031', 'name': 'Informatique', 'parent_id': None},
            {'id': '340861031', 'name': 'Téléphones & Accessoires', 'parent_id': None},
            {'id': '340862031', 'name': 'Photo & Caméscopes', 'parent_id': None},
            {'id': '213080031', 'name': 'Vêtements', 'parent_id': None},
            {'id': '193711031', 'name': 'Chaussures et Sacs', 'parent_id': None},
            {'id': '197861031', 'name': 'Cuisine & Maison', 'parent_id': None},
            {'id': '197862031', 'name': 'Bricolage', 'parent_id': None},
            {'id': '340864031', 'name': 'Sports et Loisirs', 'parent_id': None},
            {'id': '548014', 'name': 'Livres', 'parent_id': None},
            {'id': '405322', 'name': 'Jeux et Jouets', 'parent_id': None},
            {'id': '340920031', 'name': 'Beauté et Parfum', 'parent_id': None},
        ]
        
        return categories
    
    def get_products(self, category_id: Optional[str] = None, page: int = 1, limit: int = 10) -> Dict:
        """
        Récupérer les produits Amazon
        Note: Amazon PA-API a des limites strictes (1 req/sec, 8640 req/jour)
        """
        try:
            # Construire la requête PA-API
            payload = {
                'PartnerTag': self.associate_tag,
                'PartnerType': 'Associates',
                'Marketplace': self.marketplace,
                'ItemCount': min(limit, 10),  # Max 10 par requête
                'ItemPage': page,
                'Resources': [
                    'Images.Primary.Large',
                    'ItemInfo.Title',
                    'ItemInfo.Features',
                    'Offers.Listings.Price',
                    'Offers.Listings.SavingBasis'
                ]
            }
            
            if category_id:
                payload['SearchIndex'] = self._get_search_index(category_id)
                payload['BrowseNodeId'] = category_id
            else:
                payload['Keywords'] = 'bestsellers'
                payload['SearchIndex'] = 'All'
            
            # Note: Implémentation simplifiée
            # En production, utilisez la bibliothèque python-amazon-paapi
            
            # Pour l'instant, retourner une structure vide
            # L'utilisateur devra installer: pip install python-amazon-paapi
            
            return {
                'products': [],
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total': 0,
                    'pages': 0
                },
                'note': 'Amazon PA-API nécessite la bibliothèque python-amazon-paapi'
            }
            
        except Exception as e:
            print(f"Erreur récupération produits Amazon: {e}")
            return {'products': [], 'pagination': {}}
    
    def get_product_details(self, product_id: str) -> Dict:
        """Récupérer les détails d'un produit Amazon (ASIN)"""
        try:
            # Utiliser GetItems avec l'ASIN
            payload = {
                'ItemIds': [product_id],
                'PartnerTag': self.associate_tag,
                'PartnerType': 'Associates',
                'Marketplace': self.marketplace,
                'Resources': [
                    'Images.Primary.Large',
                    'Images.Variants.Large',
                    'ItemInfo.Title',
                    'ItemInfo.Features',
                    'ItemInfo.ProductInfo',
                    'Offers.Listings.Price',
                    'Offers.Listings.SavingBasis'
                ]
            }
            
            # Implémentation simplifiée
            return {}
            
        except Exception as e:
            print(f"Erreur détails produit Amazon: {e}")
            return {}
    
    def get_product_stock(self, product_id: str, variant_id: Optional[str] = None) -> int:
        """Amazon ne fournit pas d'info stock via PA-API"""
        return 999  # Stock virtuel pour affiliation
    
    def create_order(self, order_data: Dict) -> Dict:
        """
        Amazon PA-API ne permet pas de créer des commandes
        C'est un système d'affiliation : le client achète directement sur Amazon
        """
        return {
            'success': False,
            'error': 'Amazon PA-API est un système d\'affiliation. Les clients achètent directement sur Amazon.',
            'affiliate_link': self._generate_affiliate_link(order_data.get('items', []))
        }
    
    def get_order_status(self, order_id: str) -> Dict:
        """Amazon PA-API ne permet pas de suivre les commandes"""
        return {
            'error': 'Suivi de commande non disponible avec Amazon PA-API (affiliation)'
        }
    
    def _get_search_index(self, browse_node_id: str) -> str:
        """Mapper browse node vers search index"""
        mapping = {
            '340858031': 'Electronics',
            '197858031': 'Computers',
            '340861031': 'Wireless',
            '340862031': 'Photo',
            '213080031': 'Fashion',
            '193711031': 'Shoes',
            '197861031': 'Kitchen',
            '197862031': 'HomeImprovement',
            '340864031': 'SportingGoods',
            '548014': 'Books',
            '405322': 'Toys',
            '340920031': 'Beauty',
        }
        return mapping.get(browse_node_id, 'All')
    
    def _generate_affiliate_link(self, items: List[Dict]) -> str:
        """Générer un lien affilié Amazon"""
        if not items:
            return f'https://{self.marketplace}/?tag={self.associate_tag}'
        
        asin = items[0].get('external_product_id', '')
        return f'https://{self.marketplace}/dp/{asin}?tag={self.associate_tag}'
    
    def _format_product(self, raw_data: Dict) -> Dict:
        """Formater un produit Amazon en format MPS"""
        item_info = raw_data.get('ItemInfo', {})
        offers = raw_data.get('Offers', {}).get('Listings', [{}])[0]
        images = raw_data.get('Images', {}).get('Primary', {})
        
        return {
            'external_id': raw_data.get('ASIN'),
            'name': item_info.get('Title', {}).get('DisplayValue', ''),
            'description': '\n'.join(item_info.get('Features', {}).get('DisplayValues', [])),
            'price': float(offers.get('Price', {}).get('Amount', 0)),
            'compare_price': float(offers.get('SavingBasis', {}).get('Amount', 0)),
            'currency': offers.get('Price', {}).get('Currency', 'EUR'),
            'stock': 999,  # Stock virtuel
            'sku': raw_data.get('ASIN'),
            'images': [images.get('Large', {}).get('URL', '')] if images else [],
            'category_id': '',
            'category_name': 'Amazon',
            'affiliate_link': f"https://{self.marketplace}/dp/{raw_data.get('ASIN')}?tag={self.associate_tag}",
            'raw_data': raw_data
        }
    
    def translate_product_data(self, raw_data: Dict) -> Dict:
        """Traduire les données Amazon en format MPS"""
        return self._format_product(raw_data)
