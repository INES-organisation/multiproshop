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
from flask import has_app_context, has_request_context
import logging
import re
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


def _shared_get(key):
    """Cache de l'app (Redis en production), partagé par les processus web et Celery"""
    if not has_app_context():
        return None
    try:
        from extensions import cache
        return cache.get(key)
    except Exception:
        return None


def _shared_set(key, value, timeout):
    if not has_app_context():
        return
    try:
        from extensions import cache
        cache.set(key, value, timeout=max(int(timeout), 1))
    except Exception:
        pass


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
        # Pendant une requête web, on échoue vite plutôt que de faire attendre le client
        self.fail_fast = has_request_context()
        self.timeout = 10 if self.fail_fast else 30
        self.verify_ssl = False
        
    def get_access_token(self) -> Optional[str]:
        """
        Token CJ partagé entre tous les processus (cache Redis de l'app), sinon mémoire du processus.
        CJ n'accepte qu'une authentification toutes les 5 minutes : pendant une requête web on
        n'attend jamais (le client verrait une page bloquée puis une 504), on renvoie None tout de suite.
        """
        now = time.time()
        shared = _shared_get('cj:access_token')
        if shared and shared.get('expires', 0) > now:
            _memory_cache['access_token'], _memory_cache['token_expires_at'] = shared['token'], shared['expires']
            return shared['token']
        if _memory_cache['access_token'] and _memory_cache['token_expires_at'] > now:
            return _memory_cache['access_token']

        last_auth = max(_memory_cache['last_auth_call'], _shared_get('cj:last_auth') or 0)
        blocked_until = max(_memory_cache['rate_limit_until'], _shared_get('cj:rate_limit_until') or 0,
                            last_auth + 300 if last_auth else 0)
        if blocked_until > now:
            if self.fail_fast:
                logger.warning(f"[CJ API] Authentification CJ indisponible encore {blocked_until - now:.0f}s - abandon")
                return None
            logger.warning(f"[CJ API] Auth limitée à 1x/5min - attente {blocked_until - now:.0f}s...")
            time.sleep(blocked_until - now)
            shared = _shared_get('cj:access_token')  # un autre processus a pu s'authentifier entre-temps
            if shared and shared.get('expires', 0) > time.time():
                return shared['token']

        try:
            logger.info(f"[CJ API] Authentification avec email: {self.email}")
            _memory_cache['last_auth_call'] = time.time()
            _shared_set('cj:last_auth', _memory_cache['last_auth_call'], 300)

            url = f"{self.base_url}/authentication/getAccessToken"
            # NOTE: Ne PAS envoyer CJ-DEV-KEY lors de l'authentification
            # CJ rejette avec "APIkey is wrong" si présent
            auth_data = {'email': self.email, 'password': self.password}
            response = requests.post(url, json=auth_data, headers={'Content-Type': 'application/json'},
                                     verify=self.verify_ssl, timeout=self.timeout)
            logger.info(f"[CJ API] Réponse HTTP: {response.status_code}")

            if response.status_code == 429:
                logger.warning("[CJ API] Rate limit 429 sur auth - nouvel essai dans 5 min")
                self._block(300)
                return None

            if response.status_code == 200:
                data = response.json()
                if data.get('result') is False:
                    logger.error(f"[CJ API] Erreur: {data.get('message')}")
                    if data.get('code') == 1600200:
                        logger.warning("[CJ API] Rate limit code 1600200 détecté - pause 60s")
                        self._block(60)
                    return None

                if 'data' in data and 'accessToken' in data['data']:
                    token = data['data']['accessToken']
                    expiry_date = data['data'].get('accessTokenExpiryDate')
                    # Calculer expiration (avec marge de 60s)
                    if expiry_date:
                        expiry_timestamp = datetime.fromisoformat(expiry_date.replace('Z', '+00:00')).timestamp() - 60
                    else:
                        expiry_timestamp = time.time() + (14 * 24 * 3600)  # 14 jours par défaut
                    _memory_cache['access_token'] = token
                    _memory_cache['token_expires_at'] = expiry_timestamp
                    _shared_set('cj:access_token', {'token': token, 'expires': expiry_timestamp},
                                int(expiry_timestamp - time.time()))
                    # Synchroniser le rate limiter global après auth
                    _memory_cache['last_api_call'] = time.time()
                    logger.info("[CJ API] Authentification réussie !")
                    return token

            logger.error(f"[CJ API] Échec authentification: {response.status_code}")
            return None

        except Exception as e:
            logger.error(f"[CJ API] Exception getAccessToken: {e}")
            return None

    def _block(self, seconds: int):
        """Pause imposée par CJ, partagée entre processus"""
        _memory_cache['rate_limit_until'] = time.time() + seconds
        _shared_set('cj:rate_limit_until', _memory_cache['rate_limit_until'], seconds)

    def refresh_access_token(self) -> Optional[str]:
        """Rafraîchir le token d'accès"""
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
        if self.fail_fast:
            max_retries = 1  # requête web : une seule tentative, le client n'attend pas

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
                    if self.fail_fast:
                        self._block(60)
                        return None
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
                    if self.fail_fast:
                        self._block(60)
                        return None
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
    
    def get_variant_inventory(self, vid: str) -> Optional[List[Dict]]:
        """
        Stock d'une variante par entrepôt (product/stock/queryByVid).
        product/query ne renvoie pas le stock (inventories et inventoryNum valent None) : c'est la seule source.
        """
        response = self._make_request('GET', 'product/stock/queryByVid', params={'vid': vid})
        if not response or response.get('result') is False:
            return None
        return [
            {'country': w.get('countryCode', ''), 'total': int(w.get('totalInventoryNum') or 0)}
            for w in (response.get('data') or [])
        ]

    def get_stock(self, variants: List[Dict], enough: int = None, max_variants: int = 10) -> Optional[Dict]:
        """
        Stock d'un produit = somme du stock de ses variantes, tous entrepôts, dont la part en France.
        S'arrête dès que `enough` est atteint (un appel par variante). None si aucune réponse de CJ :
        stock inconnu, à ne pas confondre avec un stock nul.
        """
        total, france, answered = 0, 0, False
        for variant in [v for v in variants if v.get('vid')][:max_variants]:
            warehouses = self.get_variant_inventory(variant['vid'])
            if warehouses is None:
                continue
            answered = True
            total += sum(w['total'] for w in warehouses)
            france += sum(w['total'] for w in warehouses if w['country'] == 'FR')
            if enough is not None and total >= enough:
                break
        return {'total': total, 'france': france} if answered else None

    def calculate_shipping(self, products: List[Dict], country_code: str = 'FR',
                           start_country: str = 'CN') -> Optional[Dict]:
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
                'startCountryCode': start_country,
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
            # Plage entre variantes : « 3.62 -- 7.16 » ou « 3.62-7.16 » → borne basse, comme avant
            numbers = re.findall(r'\d+(?:\.\d+)?', str(price_value))
            return float(numbers[0]) if numbers else 0.0
        
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
