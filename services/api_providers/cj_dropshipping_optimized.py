"""
Intégration CJ Dropshipping API - Version Optimisée
Inspirée du projet TonyAlpha80 avec cache token et rate limiting
Documentation: https://developers.cjdropshipping.com/
"""
from typing import List, Dict, Optional
import os
import requests
import time
from datetime import datetime, timedelta
from flask import session, has_request_context
import logging
import random

logger = logging.getLogger(__name__)

# Cache en mémoire pour utilisation hors contexte HTTP
_memory_cache = {
    'access_token': None,
    'token_expires_at': 0,
    'rate_limit_until': 0,
    'last_api_call': 0,          # timestamp du dernier appel API
    'min_interval': 1.5,         # intervalle minimum entre appels (Free CJ = 1 req/s)
    'last_auth_call': 0,         # timestamp du dernier appel auth
}


class CJDropshippingApiOptimized:
    """
    API CJ Dropshipping optimisée avec:
    - Cache token en session Flask (contexte HTTP)
    - Cache mémoire (hors contexte HTTP)
    - Gestion rate limiting (429)
    - Fallback sur erreurs
    - Méthodes complètes
    """
    
    def __init__(self, email: str = None, password: str = None, dev_key: str = None, provider=None):
        """
        Initialiser l'API CJ
        
        Args:
            email: Email CJ Dropshipping
            password: Mot de passe CJ Dropshipping
            dev_key: Clé développeur (optionnel)
            provider: Objet ApiProvider (alternative aux paramètres individuels)
        """
        # Support pour les deux modes d'initialisation
        if provider is None and email is not None and not isinstance(email, str):
            provider, email = email, None  # appel historique CJDropshippingProvider(provider)
        if provider is not None:
            # Mode provider : CJDropshippingApiOptimized(provider=provider)
            # Clés gérées dans INES (chargées dans l'environnement par config.py) prioritaires
            # sur celles enregistrées en base pour le fournisseur
            self.email = os.getenv('CJ_EMAIL') or provider.api_key  # email stocké dans api_key
            self.password = os.getenv('CJ_PASSWORD') or provider.api_secret  # password stocké dans api_secret
            self.dev_key = os.getenv('CJ_DEV_KEY') or getattr(provider, 'dev_key', None)
        else:
            # Mode direct : CJDropshippingApiOptimized(email=..., password=...)
            self.email = email
            self.password = password
            self.dev_key = dev_key
        
        self.base_url = 'https://developers.cjdropshipping.com/api2.0/v1'
        self.timeout = 30
        self.verify_ssl = False
        self.use_session = has_request_context()
        
    def get_access_token(self) -> Optional[str]:
        """
        Obtenir un access token CJ avec cache en session ou mémoire
        Inspiré de TonyAlpha80/src/Api/v1/Services/CjDropshippingApi.php
        """
        # Utiliser session Flask si disponible, sinon cache mémoire
        if self.use_session:
            # Vérifier rate limiting - attendre au lieu de retourner None
            if 'cj_rate_limit_until' in session:
                wait = session['cj_rate_limit_until'] - time.time()
                if wait > 0:
                    logger.warning(f"[CJ API] Rate limit actif - attente {wait:.0f}s...")
                    time.sleep(wait)
                    del session['cj_rate_limit_until']
            
            # Vérifier token en cache
            if 'cj_access_token' in session and 'cj_token_expires_at' in session:
                if session['cj_token_expires_at'] > time.time():
                    return session['cj_access_token']
        else:
            # Utiliser cache mémoire - attendre au lieu de retourner None
            wait = _memory_cache['rate_limit_until'] - time.time()
            if wait > 0:
                logger.warning(f"[CJ API] Rate limit actif - attente {wait:.0f}s...")
                time.sleep(wait)
                _memory_cache['rate_limit_until'] = 0
            
            if _memory_cache['access_token'] and _memory_cache['token_expires_at'] > time.time():
                return _memory_cache['access_token']
        
        # Obtenir nouveau token - respecter limite 1x/5min
        try:
            # Vérifier si on a fait un appel auth récemment (< 5 min)
            since_last_auth = time.time() - _memory_cache['last_auth_call']
            if since_last_auth < 300 and _memory_cache['last_auth_call'] > 0:
                wait = 300 - since_last_auth
                logger.warning(f"[CJ API] Auth limitée à 1x/5min - attente {wait:.0f}s...")
                time.sleep(wait)
            
            logger.info(f"[CJ API] Authentification avec email: {self.email}")
            _memory_cache['last_auth_call'] = time.time()
            
            url = f"{self.base_url}/authentication/getAccessToken"
            
            headers = {
                'Content-Type': 'application/json'
            }
            
            # NOTE: Ne PAS envoyer CJ-DEV-KEY lors de l'authentification
            # CJ rejette avec "APIkey is wrong" si présent
            
            auth_data = {
                'email': self.email,
                'password': self.password
            }
            
            response = requests.post(
                url,
                json=auth_data,
                headers=headers,
                verify=self.verify_ssl,
                timeout=self.timeout
            )
            
            logger.info(f"[CJ API] Réponse HTTP: {response.status_code}")
            
            # Gestion rate limiting (429) - Avant de parser JSON
            if response.status_code == 429:
                wait_time = 300
                logger.warning(f"[CJ API] Rate limit 429 sur auth - attente {wait_time // 60} min...")
                time.sleep(wait_time)
                # Retenter une fois après l'attente
                response = requests.post(url, json=auth_data, headers=headers, verify=self.verify_ssl, timeout=self.timeout)
                if response.status_code == 429:
                    logger.error("[CJ API] Rate limit 429 persistant après 5 min - attente 5 min supplémentaires")
                    if self.use_session:
                        session['cj_rate_limit_until'] = time.time() + 300
                    else:
                        _memory_cache['rate_limit_until'] = time.time() + 300
                    return None
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('result') is False:
                    logger.error(f"[CJ API] Erreur: {data.get('message')}")
                    
                    # Gestion rate limiting via code erreur
                    if data.get('code') == 1600200:
                        logger.warning("[CJ API] Rate limit code 1600200 détecté - attente 60s")
                        if self.use_session:
                            session['cj_rate_limit_until'] = time.time() + 60
                        else:
                            _memory_cache['rate_limit_until'] = time.time() + 60
                    
                    return None
                
                if 'data' in data and 'accessToken' in data['data']:
                    token = data['data']['accessToken']
                    expiry_date = data['data'].get('accessTokenExpiryDate')
                    
                    # Calculer expiration (avec marge de 60s)
                    if expiry_date:
                        expiry_timestamp = datetime.fromisoformat(expiry_date.replace('Z', '+00:00')).timestamp() - 60
                    else:
                        expiry_timestamp = time.time() + (14 * 24 * 3600)  # 14 jours par défaut
                    
                    # Stocker en session ou mémoire selon le contexte
                    if self.use_session:
                        session['cj_access_token'] = token
                        session['cj_token_expires_at'] = expiry_timestamp
                        
                        if 'refreshToken' in data['data']:
                            session['cj_refresh_token'] = data['data']['refreshToken']
                    else:
                        _memory_cache['access_token'] = token
                        _memory_cache['token_expires_at'] = expiry_timestamp
                    
                    # Synchroniser le rate limiter global après auth
                    _memory_cache['last_api_call'] = time.time()
                    logger.info("[CJ API] Authentification réussie !")
                    return token
            
            logger.error(f"[CJ API] Échec authentification: {response.status_code}")
            return None
            
        except Exception as e:
            logger.error(f"[CJ API] Exception getAccessToken: {e}")
            return None
    
    def refresh_access_token(self) -> Optional[str]:
        """Rafraîchir le token d'accès"""
        if 'cj_refresh_token' not in session:
            return self.get_access_token()
        
        try:
            url = f"{self.base_url}/authentication/refreshAccessToken"
            
            response = requests.post(
                url,
                json={'refreshToken': session['cj_refresh_token']},
                headers={'Content-Type': 'application/json'},
                verify=self.verify_ssl,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and 'accessToken' in data['data']:
                    token = data['data']['accessToken']
                    expiry_date = data['data'].get('accessTokenExpiryDate')
                    
                    if expiry_date:
                        expiry_timestamp = datetime.fromisoformat(expiry_date.replace('Z', '+00:00')).timestamp() - 60
                    else:
                        expiry_timestamp = time.time() + (14 * 24 * 3600)
                    
                    session['cj_access_token'] = token
                    session['cj_token_expires_at'] = expiry_timestamp
                    
                    return token
            
            return self.get_access_token()
            
        except Exception as e:
            logger.error(f"[CJ API] Erreur refresh token: {e}")
            return self.get_access_token()
    
    def _make_request(self, method: str, endpoint: str, max_retries: int = 2, **kwargs) -> Optional[Dict]:
        """
        Effectuer une requête API avec retry et backoff exponentiel
        
        Args:
            method: Méthode HTTP (GET, POST)
            endpoint: Endpoint API
            max_retries: Nombre max de tentatives (défaut: 3)
            **kwargs: Arguments pour requests
            
        Returns:
            Dict avec la réponse ou None si échec
        """
        token = self.get_access_token()
        if not token:
            return None
        
        url = f"{self.base_url}/{endpoint}"
        
        if 'headers' not in kwargs:
            kwargs['headers'] = {}
        
        kwargs['headers']['CJ-Access-Token'] = token
        kwargs['headers']['Content-Type'] = 'application/json'
        
        if self.dev_key:
            kwargs['headers']['CJ-DEV-KEY'] = self.dev_key
        
        kwargs['verify'] = self.verify_ssl
        kwargs['timeout'] = self.timeout
        
        # Retry avec backoff exponentiel
        for attempt in range(max_retries):
            try:
                # Rate limiter global: 1.5s minimum entre chaque appel API (Free CJ = 1 req/s)
                elapsed = time.time() - _memory_cache['last_api_call']
                min_interval = _memory_cache['min_interval']
                if elapsed < min_interval:
                    time.sleep(min_interval - elapsed)
                _memory_cache['last_api_call'] = time.time()
                
                if method.upper() == 'GET':
                    response = requests.get(url, **kwargs)
                elif method.upper() == 'POST':
                    response = requests.post(url, **kwargs)
                else:
                    raise ValueError(f"Méthode HTTP non supportée: {method}")
                
                # Gérer rate limiting (429)
                if response.status_code == 429:
                    logger.warning(f"[CJ API] 429 body: {response.text[:300]}")
                    if attempt < max_retries - 1:
                        # Attente longue fixe de 10 min - chaque retry court relance le compteur CJ
                        wait_time = 600
                        logger.warning(f"[CJ API] Rate limit 429 - attente {wait_time // 60} min (retry {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"[CJ API] Rate limit 429 - max retries atteint après {max_retries} tentatives")
                        return None
                
                # Gérer erreurs serveur (5xx)
                if 500 <= response.status_code < 600:
                    if attempt < max_retries - 1:
                        wait_time = (2 ** attempt) + random.uniform(0, 1)
                        logger.warning(f"[CJ API] Erreur serveur {response.status_code} - retry {attempt + 1}/{max_retries} dans {wait_time:.1f}s")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"[CJ API] Erreur serveur {response.status_code} - max retries atteint")
                        return None
                
                # Nettoyer la réponse JSON (supprimer caractères avant {)
                response_text = response.text
                if response_text:
                    start_idx = response_text.find('{')
                    if start_idx > 0:
                        response_text = response_text[start_idx:]
                
                data = response.json() if response_text else {}
                
                # Vérifier si CJ retourne une erreur dans le JSON
                if isinstance(data, dict) and data.get('code') == 1600200:
                    # Code 1600200 = rate limit dans la réponse JSON
                    if attempt < max_retries - 1:
                        wait_time = 600
                        logger.warning(f"[CJ API] Rate limit code 1600200 - attente {wait_time // 60} min (retry {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"[CJ API] Rate limit code 1600200 - max retries atteint")
                        return None
                
                # Succès
                return data
                
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(f"[CJ API] Timeout - retry {attempt + 1}/{max_retries} dans {wait_time:.1f}s")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"[CJ API] Timeout - max retries atteint")
                    return None
                    
            except requests.exceptions.ConnectionError:
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(f"[CJ API] Erreur connexion - retry {attempt + 1}/{max_retries} dans {wait_time:.1f}s")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"[CJ API] Erreur connexion - max retries atteint")
                    return None
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(f"[CJ API] Erreur {e} - retry {attempt + 1}/{max_retries} dans {wait_time:.1f}s")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"[CJ API] Erreur requête {method} {endpoint}: {e}")
                    return None
        
        return None
    
    def get_categories(self) -> List[Dict]:
        """
        Récupérer les catégories CJ avec structure hiérarchique
        Retourne 3 niveaux: categoryFirst > categorySecond > category
        """
        try:
            response = self._make_request('GET', 'product/getCategory')
            
            if not response or response.get('result') is False:
                return []
            
            categories = []
            data = response.get('data', [])
            
            # Structure hiérarchique CJ
            for first_level in data:
                first_id = first_level.get('categoryFirstId', '')
                first_name = first_level.get('categoryFirstName', '')
                
                # Ajouter niveau 1
                categories.append({
                    'id': first_id,
                    'cj_category_id': first_id,
                    'name': first_name,
                    'parent_id': None,
                    'level': 1,
                    'product_count': 0,
                    'path': first_name
                })
                
                for second_level in first_level.get('categoryFirstList', []):
                    second_id = second_level.get('categorySecondId', '')
                    second_name = second_level.get('categorySecondName', '')
                    
                    # Ajouter niveau 2
                    categories.append({
                        'id': second_id,
                        'cj_category_id': second_id,
                        'name': second_name,
                        'parent_id': first_id,
                        'level': 2,
                        'product_count': 0,
                        'path': f"{first_name} > {second_name}"
                    })
                    
                    for category in second_level.get('categorySecondList', []):
                        cat_id = category.get('categoryId', '')
                        cat_name = category.get('categoryName', '')
                        
                        # Ajouter niveau 3
                        categories.append({
                            'id': cat_id,
                            'cj_category_id': cat_id,
                            'name': cat_name,
                            'parent_id': second_id,
                            'level': 3,
                            'product_count': 0,
                            'path': f"{first_name} > {second_name} > {cat_name}"
                        })
            
            return categories
            
        except Exception as e:
            logger.error(f"[CJ API] Erreur get_categories: {e}")
            return []
    
    def get_products(self, page: int = 1, page_size: int = 20, filters: Dict = None) -> Dict:
        """
        Récupérer les produits CJ avec pagination
        """
        params = {
            'pageNum': page,
            'pageSize': min(page_size, 100)  # CJ max 100
        }
        
        if filters:
            if 'categoryId' in filters:
                params['categoryId'] = filters['categoryId']
            if 'productName' in filters:
                params['productName'] = filters['productName']
        
        try:
            response = self._make_request('GET', 'product/list', params=params)
            
            if not response or response.get('result') is False:
                return {'products': [], 'total': 0, 'page': page}
            
            data = response.get('data', {})
            products_list = data.get('list', [])
            
            # Formater les produits
            formatted_products = []
            for product in products_list:
                formatted = self._format_product(product)
                formatted_products.append(formatted)
            
            return {
                'products': formatted_products,
                'total': data.get('total', 0),
                'page': page,
                'page_size': page_size,
                'total_pages': (data.get('total', 0) + page_size - 1) // page_size
            }
            
        except Exception as e:
            logger.error(f"[CJ API] Erreur get_products: {e}")
            return {'products': [], 'total': 0, 'page': page}
    
    def get_products_v2(self, page: int = 1, page_size: int = 20, keyword: str = None, category_id: str = None) -> Dict:
        """
        Récupérer les produits via listV2 (inclut warehouseInventoryNum pour le stock)
        """
        params = {
            'page': page,
            'size': min(page_size, 100)
        }
        
        if keyword:
            params['keyWord'] = keyword
        if category_id:
            params['categoryId'] = category_id
        
        try:
            response = self._make_request('GET', 'product/listV2', params=params)
            
            if not response or response.get('result') is False:
                return {'products': [], 'total': 0, 'page': page}
            
            data = response.get('data', {})
            content = data.get('content', [])
            
            # Extraire les produits depuis la structure content[].productList[]
            products = []
            for item in content:
                for p in item.get('productList', []):
                    # Parser le prix (peut être une plage "0.45 -- 0.88")
                    raw_price = str(p.get('sellPrice', 0) or 0)
                    try:
                        price = float(raw_price)
                    except (ValueError, TypeError):
                        # Extraire le premier nombre d'une plage
                        import re
                        nums = re.findall(r'[\d.]+', raw_price)
                        price = float(nums[0]) if nums else 0.0
                    
                    warehouse_stock = int(p.get('warehouseInventoryNum', 0) or 0)
                    verified_stock = int(p.get('totalVerifiedInventory', 0) or 0)
                    unverified_stock = int(p.get('totalUnVerifiedInventory', 0) or 0)
                    best_stock = max(warehouse_stock, verified_stock, verified_stock + unverified_stock)
                    
                    products.append({
                        'pid': p.get('id'),
                        'name': p.get('nameEn', ''),
                        'sku': p.get('sku', ''),
                        'image': p.get('bigImage', ''),
                        'price': price,
                        'stock': best_stock,
                        'category_id': p.get('categoryId'),
                    })
            
            return {
                'products': products,
                'total': data.get('totalRecords', 0),
                'page': page,
                'page_size': page_size,
                'total_pages': data.get('totalPages', 0)
            }
            
        except Exception as e:
            logger.error(f"[CJ API] Erreur get_products_v2: {e}")
            return {'products': [], 'total': 0, 'page': page}
    
    def get_product_details(self, pid: str) -> Optional[Dict]:
        """Récupérer les détails complets d'un produit"""
        try:
            response = self._make_request('GET', 'product/query', params={'pid': pid})
            
            if not response or response.get('result') is False:
                return None
            
            data = response.get('data', {})
            return self._format_product(data)
            
        except Exception as e:
            logger.error(f"[CJ API] Erreur get_product_details: {e}")
            return None
    
    def get_product_variants(self, pid: str) -> Optional[Dict]:
        """
        Récupérer les variantes d'un produit via l'endpoint dédié
        Endpoint: /api2.0/v1/product/variant/query?pid=xxx
        Inspiré de TonyAlpha80/src/Api/v1/Services/CjDropshippingApi.php:452
        """
        try:
            response = self._make_request('GET', 'product/variant/query', params={'pid': pid})
            
            if not response or response.get('result') is False:
                logger.warning(f"[CJ API] Pas de variantes pour PID {pid}")
                return None
            
            # L'API CJ retourne les variantes dans data
            return response
            
        except Exception as e:
            logger.error(f"[CJ API] Erreur get_product_variants pour {pid}: {e}")
            return None
    
    def calculate_shipping(self, products: List[Dict], country_code: str = 'FR') -> Optional[Dict]:
        """
        Calculer les frais de port CJ
        Inspiré de TonyAlpha80/src/Controllers/ShippingController.php
        """
        try:
            # Préparer les données pour CJ
            product_list = []
            for product in products:
                product_list.append({
                    'vid': product.get('vid') or product.get('id'),
                    'quantity': product.get('quantity', 1)
                })
            
            freight_data = {
                'startCountryCode': 'CN',
                'endCountryCode': country_code,
                'products': product_list
            }
            
            response = self._make_request('POST', 'logistic/freightCalculate', json=freight_data)
            
            if not response or response.get('result') is False:
                return None
            
            return response.get('data', [])
            
        except Exception as e:
            logger.error(f"[CJ API] Erreur calculate_shipping: {e}")
            return None
    
    def get_product_comments(self, pid: str, page: int = 1, page_size: int = 20) -> List[Dict]:
        """Récupérer les avis clients d'un produit"""
        try:
            params = {
                'pid': pid,
                'pageNum': page,
                'pageSize': page_size
            }
            
            response = self._make_request('GET', 'product/comment/list', params=params)
            
            if not response or response.get('result') is False:
                return []
            
            data = response.get('data', {})
            comments = data.get('list', [])
            
            # Formater les avis
            formatted_comments = []
            for comment in comments:
                formatted_comments.append({
                    'id': comment.get('commentId'),
                    'rating': comment.get('star', 0),
                    'content': comment.get('content', ''),
                    'author': comment.get('userName', 'Anonymous'),
                    'date': comment.get('createTime', ''),
                    'images': comment.get('images', [])
                })
            
            return formatted_comments
            
        except Exception as e:
            logger.error(f"[CJ API] Erreur get_product_comments: {e}")
            return []
    
    def create_order(self, order_data: Dict) -> Dict:
        """Créer une commande chez CJ"""
        try:
            response = self._make_request('POST', 'shopping/order/createOrder', json=order_data)
            
            if not response or response.get('result') is False:
                return {
                    'success': False,
                    'error': response.get('message', 'Erreur création commande')
                }
            
            data = response.get('data', {})
            return {
                'success': True,
                'order_id': data.get('orderId'),
                'order_number': data.get('orderNum')
            }
            
        except Exception as e:
            logger.error(f"[CJ API] Erreur create_order: {e}")
            return {'success': False, 'error': str(e)}
    
    def _format_product(self, raw_data: Dict) -> Dict:
        """
        Formater un produit CJ en format standardisé
        Inspiré de TonyAlpha80/src/Api/v1/Services/CjDropshippingApi.php
        """
        # Gérer les noms multilingues
        product_name = raw_data.get('productNameEn', '')
        if not product_name:
            product_name = raw_data.get('productName', '')
            # Si JSON array, prendre le premier
            if isinstance(product_name, str) and product_name.startswith('['):
                try:
                    import json
                    names = json.loads(product_name)
                    product_name = names[0] if names else 'Produit sans nom'
                except:
                    pass
        
        # Gérer les prix (peuvent être des plages "3.62 -- 7.16")
        def parse_price(price_value):
            if not price_value:
                return 0.0
            price_str = str(price_value).strip()
            if '--' in price_str:
                price_str = price_str.split('--')[0].strip()
            try:
                return float(price_str)
            except:
                return 0.0
        
        # Images
        images = []
        product_image = raw_data.get('productImage')
        if product_image:
            if isinstance(product_image, str):
                # Peut être un JSON array: '["url1", "url2"]'
                stripped = product_image.strip()
                if stripped.startswith('['):
                    try:
                        import json
                        parsed = json.loads(stripped)
                        if isinstance(parsed, list):
                            images.extend(parsed)
                        else:
                            images.append(product_image)
                    except (json.JSONDecodeError, ValueError):
                        images.append(product_image)
                else:
                    images.append(product_image)
            elif isinstance(product_image, list):
                images.extend(product_image)
        
        # Variantes
        variants = []
        for variant in raw_data.get('variants', []):
            # Extraire le stock depuis inventories (structure CJ API v2)
            variant_stock = 0
            inventories = variant.get('inventories')
            if inventories and isinstance(inventories, list):
                for inv in inventories:
                    variant_stock += int(inv.get('totalInventory', 0) or 0)
            
            # Fallback sur d'autres clés de stock
            if variant_stock == 0:
                variant_stock = int(variant.get('variantQuantity', 0) or variant.get('inventoryNum', 0) or 0)
            
            variants.append({
                'vid': variant.get('vid'),
                'key': variant.get('variantKey', ''),
                'sku': variant.get('variantSku', ''),
                'price': parse_price(variant.get('variantSellPrice')),
                'suggested_price': parse_price(variant.get('variantSugSellPrice')),
                'stock': variant_stock,
                'image': variant.get('variantImage', ''),
                'weight': variant.get('variantWeight', 0),
                'variantNameEn': variant.get('variantNameEn', ''),
                'inventories': inventories
            })
        
        # Stock produit = somme des stocks variantes (seule source fiable depuis product/query)
        total_variant_stock = sum(v.get('stock', 0) for v in variants)
        
        return {
            'pid': raw_data.get('pid'),
            'name': product_name,
            'name_en': raw_data.get('productNameEn', ''),
            'sku': raw_data.get('productSku', ''),
            'category_id': raw_data.get('categoryId'),
            'category_name': raw_data.get('categoryName', ''),
            'price': parse_price(raw_data.get('sellPrice')),
            'suggested_price': parse_price(raw_data.get('suggestSellPrice')),
            'stock': total_variant_stock,
            'image': images[0] if images else '',
            'images': images,
            'description': raw_data.get('description', ''),
            'variants': variants,
            'weight': raw_data.get('productWeight', ''),
            'material': raw_data.get('material', ''),
            'raw_data': raw_data
        }


# Alias pour compatibilité avec les imports existants
CJDropshippingProvider = CJDropshippingApiOptimized
