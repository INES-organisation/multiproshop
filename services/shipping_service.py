"""
Service de calcul des frais de livraison CJ Dropshipping
Stratégie hybride : DB cache + refresh API CJ si expiré + fallback
"""
from typing import List, Dict, Optional
from config import Config
import logging

logger = logging.getLogger(__name__)

# Âge max du cache en jours avant refresh automatique
CACHE_MAX_AGE_DAYS = 7

# Taux de conversion USD → EUR (approximatif, à ajuster)
USD_TO_EUR = 0.92


class ShippingService:
    """
    Service de calcul des frais de livraison
    Stratégie hybride :
      1. Lire le cache DB (ShippingRate) pour chaque produit du panier
      2. Si expiré (> 7 jours) ou absent → appeler l'API CJ et stocker
      3. Fusionner les méthodes communes à tous les produits du panier
      4. Fallback sur méthodes standard si rien ne fonctionne
    """
    
    # Méthodes de livraison par défaut (fallback)
    FALLBACK_METHODS = [
        {
            'code': 'STANDARD',
            'name': 'Livraison Standard',
            'price': 4.99,
            'delivery_time': '10-20 jours',
            'description': 'Livraison économique'
        },
        {
            'code': 'EXPRESS',
            'name': 'Livraison Express',
            'price': 12.99,
            'delivery_time': '5-10 jours',
            'description': 'Livraison rapide'
        },
        {
            'code': 'PREMIUM',
            'name': 'Livraison Premium',
            'price': 24.99,
            'delivery_time': '3-5 jours',
            'description': 'Livraison ultra-rapide avec suivi'
        }
    ]
    
    def __init__(self):
        """Initialiser le service"""
        self.cj_api = None
        try:
            from services.api_providers.cj_dropshipping_optimized import CJDropshippingApiOptimized
            self.cj_api = CJDropshippingApiOptimized(
                email=Config.CJ_EMAIL,
                password=Config.CJ_PASSWORD,
                dev_key=Config.CJ_DEV_KEY
            )
        except Exception as e:
            logger.warning(f"[Shipping] Impossible d'initialiser API CJ: {e}")
    
    def calculate_shipping(self, cart_items: List[Dict], country_code: str = 'FR') -> Dict:
        """
        Calculer les frais de livraison pour un panier.
        Stratégie hybride : DB cache → API CJ refresh → fallback.
        
        Args:
            cart_items: [{'product_id': int, 'cj_pid': str, 'quantity': int, 'product': {...}}]
            country_code: Code pays ISO
        
        Returns:
            {'success': bool, 'methods': [...], 'source': 'cache'|'cj'|'fallback'}
        """
        try:
            from models.shipping_rate import ShippingRate
            from extensions import db
            
            # Extraire les product_ids du panier
            product_ids = []
            for item in cart_items:
                pid = item.get('product_id')
                if not pid:
                    product = item.get('product')
                    if product:
                        pid = getattr(product, 'id', None) or product.get('id')
                if pid:
                    product_ids.append(pid)
            
            if not product_ids:
                return self._fallback_response(cart_items, country_code)

            # 0. Tarif CJ du panier entier, tel que CJ le facturera (un seul colis)
            cart_methods = self._cart_freight(cart_items, country_code)
            if cart_methods == []:  # CJ ne livre pas ce panier vers ce pays
                return self._fallback_response(cart_items, country_code)
            if cart_methods:
                return {
                    'success': True,
                    'methods': cart_methods,
                    'total_weight': self._calculate_total_weight(cart_items),
                    'source': 'cj'
                }
            
            # 1. Lire le cache DB
            cached_rates = ShippingRate.get_for_products(product_ids, country_code)
            cached_map = {r.product_id: r for r in cached_rates}
            
            # 2. Identifier les produits sans cache ou avec cache expiré
            needs_refresh = []
            for pid in product_ids:
                rate = cached_map.get(pid)
                if not rate or rate.is_expired(CACHE_MAX_AGE_DAYS):
                    needs_refresh.append(pid)
            
            # 3. Refresh via API CJ si nécessaire
            #    Limité à 1 seul produit pour ne pas bloquer le checkout trop longtemps
            if needs_refresh and self.cj_api:
                try:
                    self._refresh_rates(needs_refresh[:1], country_code, cart_items)
                    db.session.commit()
                    cached_rates = ShippingRate.get_for_products(product_ids, country_code)
                    cached_map = {r.product_id: r for r in cached_rates}
                except Exception as e:
                    logger.warning(f"[Shipping] Refresh échoué, utilisation cache/fallback: {e}")
            
            # 4. Fusionner les méthodes de tous les produits
            all_methods = self._merge_methods(product_ids, cached_map, cart_items)
            
            if all_methods:
                source = 'cache'
                # Vérifier si au moins une méthode vient de CJ
                if any(m.get('source') == 'cj' for m in all_methods):
                    source = 'cj'
                return {
                    'success': True,
                    'methods': all_methods,
                    'total_weight': self._calculate_total_weight(cart_items),
                    'source': source
                }
            
            # 5. Fallback
            return self._fallback_response(cart_items, country_code)
            
        except Exception as e:
            logger.error(f"[Shipping] Erreur calculate_shipping: {e}")
            return self._fallback_response(cart_items, country_code, error=str(e))
    
    def _cart_freight(self, cart_items: List[Dict], country_code: str) -> Optional[List[Dict]]:
        """Tarifs CJ pour tout le panier en un appel (logistic/freightCalculate), mis en cache 6 h.
        [] = CJ ne livre pas ce panier vers ce pays ; None = pas de réponse ou article sans variante CJ,
        on se rabat alors sur le cache par produit"""
        from extensions import cache
        lines = []
        for item in cart_items:
            vid = item.get('cj_vid')
            if not vid:
                product = item.get('product')
                vid = self._first_vid(product) if product is not None and not isinstance(product, dict) else None
            if not vid:
                return None
            lines.append((vid, int(item.get('quantity', 1))))
        if not lines or not self.cj_api:
            return None
        key = 'freight:%s:%s' % (country_code, ','.join(f'{v}x{q}' for v, q in sorted(lines)))
        cached = cache.get(key)
        if cached is not None:
            return cached
        data = self.cj_api.calculate_shipping([{'vid': v, 'quantity': q} for v, q in lines], country_code)
        if data is None:  # CJ injoignable : pas de mise en cache
            return None
        methods = []
        for m in data:
            try:
                # totalPostageFee = port + taxes + frais de dédouanement, quand CJ les applique
                price_usd = float(m.get('totalPostageFee') or m.get('logisticPrice'))
            except (TypeError, ValueError):
                continue
            methods.append({
                'code': m.get('logisticName', 'UNKNOWN'),
                'name': m.get('logisticName', 'Méthode inconnue'),
                'price': round(price_usd * USD_TO_EUR, 2),
                'price_usd': price_usd,
                'delivery_time': m.get('logisticAging', 'N/A'),
                'source': 'cj'
            })
        methods.sort(key=lambda m: m['price'])
        cache.set(key, methods, timeout=6 * 3600)
        return methods

    @staticmethod
    def _first_vid(product) -> Optional[str]:
        from models.product_variant import ProductVariant
        variant = ProductVariant.query.filter_by(product_id=product.id, active=True) \
            .filter(ProductVariant.cj_vid.isnot(None)).first()
        return variant.cj_vid if variant else None

    def _get_sku_for_product(self, product) -> Optional[str]:
        """Récupérer le SKU CJ de la première variante active d'un produit"""
        from models.product_variant import ProductVariant
        variant = ProductVariant.query.filter_by(
            product_id=product.id, active=True
        ).filter(ProductVariant.sku.isnot(None), ProductVariant.sku != '').first()
        if variant and variant.sku:
            return variant.sku
        return None
    
    def _refresh_rates(self, product_ids: List[int], country_code: str, cart_items: List[Dict]):
        """Rafraîchir les taux de livraison via l'API CJ (freightCalculateTip + SKU)"""
        from models.product import Product
        from models.shipping_rate import ShippingRate
        import time
        
        products = Product.query.filter(Product.id.in_(product_ids)).all()
        
        for product in products:
            sku = self._get_sku_for_product(product)
            if not sku:
                continue
            
            try:
                freight_data = {
                    'reqDTOS': [{
                        'srcAreaCode': 'CN',
                        'destAreaCode': country_code,
                        'productProp': ['COMMON'],
                        'freightTrialSkuList': [{'skuQuantity': 1, 'sku': sku}],
                        'skuList': [sku],
                        'platforms': ['Shopify']
                    }]
                }
                
                response = self.cj_api._make_request('POST', 'logistic/freightCalculateTip', max_retries=1, json=freight_data)
                
                if response is None:
                    logger.warning(f"[Shipping] API inaccessible pour produit {product.id} -> {country_code}")
                    continue
                
                if response.get('result') is True and response.get('data'):
                    methods = []
                    for m in response['data']:
                        option = m.get('option', {})
                        price_usd = float(m.get('discountFee', m.get('postage', 0)))
                        price_eur = round(price_usd * USD_TO_EUR, 2)
                        methods.append({
                            'code': option.get('enName', m.get('logisticName', 'UNKNOWN')),
                            'name': option.get('enName', m.get('logisticName', 'Méthode inconnue')),
                            'price': price_eur,
                            'price_usd': price_usd,
                            'price_cny': float(m.get('discountFeeCNY', m.get('postageCNY', 0))),
                            'delivery_time': m.get('arrivalTime', 'N/A'),
                            'source': 'cj'
                        })
                    ShippingRate.upsert(product.id, country_code, methods, source='cj')
                    logger.info(f"[Shipping] Refresh CJ OK: produit {product.id} (sku={sku}) -> {country_code} ({len(methods)} méthodes)")
                else:
                    ShippingRate.upsert(product.id, country_code, [], source='cj_empty')
                    logger.debug(f"[Shipping] Refresh CJ vide: produit {product.id} -> {country_code}")
                
                if len(products) > 1:
                    time.sleep(1.6)
                    
            except Exception as e:
                logger.error(f"[Shipping] Erreur refresh produit {product.id}: {e}")
    
    def _merge_methods(self, product_ids: List[int], cached_map: Dict, cart_items: List[Dict]) -> List[Dict]:
        """
        Fusionner les méthodes de livraison de tous les produits du panier.
        Pour un panier multi-produits, on prend le prix le plus élevé par méthode
        (car CJ calcule par produit, le shipping réel est le max).
        """
        # Collecter les méthodes par produit
        methods_per_product = []
        for pid in product_ids:
            rate = cached_map.get(pid)
            if rate and rate.has_methods():
                methods_per_product.append(rate.methods)
        
        if not methods_per_product:
            return []
        
        # Si un seul produit, retourner ses méthodes directement
        if len(methods_per_product) == 1:
            return methods_per_product[0]
        
        # Multi-produits : trouver les méthodes communes (par nom)
        # et prendre le prix total (somme des prix par produit)
        method_names = None
        for methods in methods_per_product:
            names = {m['name'] for m in methods}
            if method_names is None:
                method_names = names
            else:
                method_names &= names  # Intersection
        
        if not method_names:
            # Aucun transporteur ne prend tout le panier : ne pas facturer le port d'un seul produit
            return []
        
        # Calculer le prix total par méthode commune
        merged = {}
        for methods in methods_per_product:
            for m in methods:
                if m['name'] in method_names:
                    if m['name'] not in merged:
                        merged[m['name']] = {
                            'code': m['code'],
                            'name': m['name'],
                            'price': 0,
                            'delivery_time': m['delivery_time'],
                            'source': m.get('source', 'cj')
                        }
                    merged[m['name']]['price'] += m['price']
        
        # Arrondir les prix
        result = list(merged.values())
        for m in result:
            m['price'] = round(m['price'], 2)
        
        # Trier par prix
        result.sort(key=lambda m: m['price'])
        return result
    
    def _fallback_response(self, cart_items, country_code, error=None):
        """Pas de tarif CJ : aucune méthode proposée. Des tarifs inventés feraient payer un port
        qui ne correspond à rien, voire vers un pays que CJ ne dessert pas"""
        logger.info(f"[Shipping] Aucun tarif CJ vers {country_code}")
        resp = {
            'success': False,
            'methods': [],
            'total_weight': self._calculate_total_weight(cart_items),
            'source': 'none',
            'message': 'Livraison indisponible vers ce pays pour ce panier'
        }
        if error:
            resp['error'] = error
        return resp
    
    def _has_cj_products(self, cart_items: List[Dict]) -> bool:
        """Vérifier si le panier contient des produits CJ"""
        return any(item.get('cj_pid') or item.get('product', {}).get('cj_pid') for item in cart_items)
    
    def _calculate_cj_shipping(self, cart_items: List[Dict], country_code: str) -> Optional[List[Dict]]:
        """Calculer les frais avec l'API CJ (appel direct, sans cache)"""
        try:
            products_data = []
            
            for item in cart_items:
                product = item.get('product', {})
                cj_pid = item.get('cj_pid') or product.get('cj_pid')
                cj_vid = item.get('cj_vid')
                quantity = item.get('quantity', 1)
                
                if cj_pid:
                    products_data.append({
                        'vid': cj_vid or cj_pid,
                        'quantity': quantity
                    })
            
            if not products_data:
                return None
            
            shipping_methods = self.cj_api.calculate_shipping(products_data, country_code)
            
            if not shipping_methods:
                return None
            
            formatted_methods = []
            for method in shipping_methods:
                formatted_methods.append({
                    'code': method.get('logisticName', 'UNKNOWN'),
                    'name': method.get('logisticName', 'Méthode inconnue'),
                    'price': float(method.get('logisticPrice', 0)),
                    'delivery_time': method.get('logisticAging', 'N/A'),
                    'description': method.get('logisticName', ''),
                    'source': 'cj'
                })
            
            return formatted_methods
            
        except Exception as e:
            logger.error(f"[Shipping] Erreur _calculate_cj_shipping: {e}")
            return None
    
    def _get_fallback_methods(self, cart_items: List[Dict], country_code: str) -> List[Dict]:
        """Obtenir les méthodes de livraison par défaut"""
        methods = []
        
        # Calculer le poids total pour ajuster les prix
        total_weight = self._calculate_total_weight(cart_items)
        weight_factor = 1.0
        
        if total_weight > 2000:  # > 2kg
            weight_factor = 1.5
        elif total_weight > 5000:  # > 5kg
            weight_factor = 2.0
        
        # Ajuster les prix selon la région du pays
        EUROPE_WEST = {
            'FR', 'BE', 'LU', 'CH', 'DE', 'AT', 'NL', 'GB', 'IE', 'MC',
            'AD', 'LI', 'GI', 'GG', 'JE', 'IM', 'SM', 'VA',
        }
        EUROPE_SOUTH = {'ES', 'PT', 'IT', 'GR', 'MT', 'CY', 'HR', 'SI'}
        EUROPE_NORTH = {'DK', 'SE', 'NO', 'FI', 'IS', 'EE', 'LV', 'LT', 'FO', 'GL'}
        EUROPE_EAST = {
            'PL', 'CZ', 'SK', 'HU', 'RO', 'BG', 'UA', 'RS', 'BA', 'ME',
            'MK', 'AL', 'MD', 'XK', 'BY', 'RU',
        }
        NORTH_AMERICA = {'US', 'CA', 'MX', 'BM', 'PM'}
        AMERICAS_CARIBBEAN = {
            'GT', 'BZ', 'HN', 'SV', 'NI', 'CR', 'PA', 'CU', 'HT', 'DO',
            'JM', 'TT', 'BB', 'BS', 'AG', 'DM', 'GD', 'KN', 'LC', 'VC',
            'AI', 'AW', 'KY', 'CW', 'GP', 'MQ', 'MS', 'PR', 'BQ', 'SX',
            'MF', 'TC', 'VG', 'VI', 'AS',
            'BR', 'AR', 'CL', 'CO', 'PE', 'EC', 'UY', 'PY', 'BO', 'VE',
            'GY', 'SR', 'GF', 'FK',
        }
        DOM_TOM_FR = {'GP', 'MQ', 'GF', 'RE', 'YT', 'PM', 'NC', 'PF', 'WF', 'MF', 'BL'}
        
        if country_code in EUROPE_WEST | EUROPE_SOUTH | DOM_TOM_FR:
            country_factor = 1.0
        elif country_code in EUROPE_NORTH | EUROPE_EAST:
            country_factor = 1.15
        elif country_code in NORTH_AMERICA:
            country_factor = 1.3
        elif country_code in AMERICAS_CARIBBEAN:
            country_factor = 1.4
        else:
            country_factor = 1.5  # Asie, Afrique, Moyen-Orient, Océanie
        
        for method in self.FALLBACK_METHODS:
            methods.append({
                'code': method['code'],
                'name': method['name'],
                'price': round(method['price'] * weight_factor * country_factor, 2),
                'delivery_time': method['delivery_time'],
                'description': method['description'],
                'source': 'fallback'
            })
        
        return methods
    
    def _calculate_total_weight(self, cart_items: List[Dict]) -> float:
        """Calculer le poids total du panier (en grammes)"""
        total_weight = 0
        
        for item in cart_items:
            product = item.get('product', {})
            quantity = item.get('quantity', 1)
            
            # Helper pour accéder aux attributs (objet SQLAlchemy ou dict)
            def _get(obj, key, default=None):
                return getattr(obj, key, None) or (obj.get(key, default) if isinstance(obj, dict) else default)
            
            # Essayer de récupérer le poids
            weight = 0
            
            # Poids depuis product_weight (peut être une plage "340-370")
            product_weight = _get(product, 'product_weight', '')
            if product_weight:
                try:
                    # Prendre la valeur moyenne si c'est une plage
                    if '-' in str(product_weight):
                        parts = str(product_weight).split('-')
                        weight = (float(parts[0]) + float(parts[1])) / 2
                    else:
                        weight = float(product_weight)
                except:
                    pass
            
            # Fallback sur weight standard
            if weight == 0:
                weight = _get(product, 'weight', 0) or 0
            
            # Si toujours pas de poids, estimer à 300g
            if weight == 0:
                weight = 300
            
            total_weight += weight * quantity
        
        return total_weight
    
    def calculate_shipping_for_product(self, product_id: int, quantity: int = 1, 
                                      country_code: str = 'FR') -> Dict:
        """
        Calculer les frais de livraison pour un produit unique
        Utile pour l'affichage sur la page produit
        """
        from models.product import Product
        
        product = Product.query.get(product_id)
        if not product:
            return {
                'success': False,
                'error': 'Produit non trouvé'
            }
        
        cart_items = [{
            'cj_pid': product.cj_pid,
            'quantity': quantity,
            'product': {
                'cj_pid': product.cj_pid,
                'product_weight': product.product_weight,
                'weight': product.weight
            }
        }]
        
        return self.calculate_shipping(cart_items, country_code)
    
    def get_cheapest_method(self, methods: List[Dict]) -> Optional[Dict]:
        """Obtenir la méthode la moins chère"""
        if not methods:
            return None
        return min(methods, key=lambda m: m['price'])
    
    def get_fastest_method(self, methods: List[Dict]) -> Optional[Dict]:
        """Obtenir la méthode la plus rapide"""
        if not methods:
            return None
        
        # Trier par code (PREMIUM < EXPRESS < STANDARD)
        priority = {'PREMIUM': 1, 'EXPRESS': 2, 'STANDARD': 3}
        return min(methods, key=lambda m: priority.get(m['code'], 999))
    
    def combine_shipping_for_multiple_suppliers(self, cart_items: List[Dict], 
                                               country_code: str = 'FR') -> Dict:
        """
        Combiner les frais de livraison pour plusieurs fournisseurs
        Inspiré de TonyAlpha80 - gestion panier multi-fournisseurs
        """
        # Séparer les items par fournisseur
        cj_items = [item for item in cart_items if self._is_cj_product(item)]
        other_items = [item for item in cart_items if not self._is_cj_product(item)]
        
        total_shipping = 0
        methods_by_supplier = {}
        
        # Calculer pour CJ
        if cj_items:
            cj_result = self.calculate_shipping(cj_items, country_code)
            if cj_result['success'] and cj_result['methods']:
                cheapest_cj = self.get_cheapest_method(cj_result['methods'])
                total_shipping += cheapest_cj['price']
                methods_by_supplier['cj'] = cheapest_cj
        
        # Calculer pour autres fournisseurs (à implémenter)
        if other_items:
            # Pour l'instant, utiliser méthode standard
            total_shipping += 4.99
            methods_by_supplier['other'] = {
                'code': 'STANDARD',
                'name': 'Livraison Standard',
                'price': 4.99,
                'source': 'fallback'
            }
        
        return {
            'success': True,
            'total_shipping': total_shipping,
            'methods_by_supplier': methods_by_supplier,
            'combined': True
        }
    
    def _is_cj_product(self, item: Dict) -> bool:
        """Vérifier si un item est un produit CJ"""
        return bool(item.get('cj_pid') or item.get('product', {}).get('cj_pid'))
