"""
Service de synchronisation en arrière-plan pour les produits CJ
Inspiré de TonyAlpha80/src/Agents/SyncAgent.php
"""
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy import and_

logger = logging.getLogger(__name__)


class BackgroundSyncService:
    """
    Service de synchronisation automatique en arrière-plan
    Gère la synchronisation progressive des produits CJ
    """
    
    def __init__(self, db, cj_api):
        self.db = db
        self.cj_api = cj_api
        self.rate_limit_seconds = 300  # 5 minutes entre chaque requête
        self.last_sync_time = None
        
    def can_make_request(self) -> bool:
        """Vérifier si on peut faire une requête (rate limit)"""
        if not self.last_sync_time:
            return True
        
        elapsed = (datetime.now() - self.last_sync_time).total_seconds()
        return elapsed >= self.rate_limit_seconds
    
    def get_wait_time(self) -> int:
        """Obtenir le temps d'attente restant avant la prochaine requête"""
        if not self.last_sync_time:
            return 0
        
        elapsed = (datetime.now() - self.last_sync_time).total_seconds()
        wait_time = max(0, self.rate_limit_seconds - elapsed)
        return int(wait_time)
    
    def record_request(self):
        """Enregistrer qu'une requête a été faite"""
        self.last_sync_time = datetime.now()
    
    def get_products_to_sync(self, limit: int = 100) -> List:
        """
        Récupérer les produits à synchroniser
        Priorité : produits jamais synchronisés, puis les plus anciens
        """
        from models.product import Product
        
        try:
            # Produits CJ actifs, triés par date de dernière sync (les plus anciens en premier)
            products = Product.query.filter(
                Product.cj_pid.isnot(None),
                Product.is_active == True
            ).order_by(
                Product.synced_at.asc().nullsfirst()
            ).limit(limit).all()
            
            return products
            
        except Exception as e:
            logger.error(f"[BackgroundSync] Erreur get_products_to_sync: {e}")
            return []
    
    def sync_batch(self, batch_size: int = 10) -> Dict:
        """
        Synchroniser un lot de produits
        
        Args:
            batch_size: Nombre de produits à synchroniser
            
        Returns:
            Résultat de la synchronisation
        """
        from models.product import Product
        from services.cj_variant_sync_service import CjVariantSyncService
        
        start_time = time.time()
        
        products = self.get_products_to_sync(batch_size)
        
        if not products:
            return {
                'success': True,
                'message': 'Aucun produit à synchroniser',
                'synced': 0,
                'failed': 0,
                'duration': 0
            }
        
        synced = 0
        failed = 0
        errors = []
        
        variant_sync_service = CjVariantSyncService(self.cj_api)
        
        for product in products:
            try:
                logger.info(f"[BackgroundSync] Sync produit {product.id} (CJ PID: {product.cj_pid})")
                
                # Récupérer détails depuis CJ API
                product_data = self.cj_api.get_product_details(product.cj_pid)
                
                if product_data and 'data' in product_data:
                    data = product_data['data']
                    
                    # Mettre à jour les données du produit
                    old_stock = product.stock
                    product.stock = int(data.get('productStock', 0) or data.get('stockQuantity', 0) or 0)
                    product.price = float(data.get('sellPrice', 0) or 0)
                    product.compare_price = float(data.get('suggestSellPrice', 0) or 0)
                    product.synced_at = datetime.now()
                    
                    # Synchroniser les variantes si présentes
                    if product.variants.count() > 0:
                        try:
                            result = variant_sync_service.sync_product_variants(product.id)
                            if result['success']:
                                # Mettre à jour stock principal depuis variantes
                                product.update_stock_from_variants()
                        except Exception as e:
                            logger.error(f"[BackgroundSync] Erreur sync variantes produit {product.id}: {e}")
                    
                    self.db.session.commit()
                    
                    synced += 1
                    logger.info(f"[BackgroundSync] ✓ Produit {product.id} synchronisé (stock: {old_stock} → {product.stock})")
                else:
                    failed += 1
                    errors.append(f"Produit {product.id}: données CJ invalides")
                
                # Enregistrer la requête pour rate limit
                self.record_request()
                
                # Pause pour éviter surcharge API
                time.sleep(0.5)
                
            except Exception as e:
                failed += 1
                error_msg = f"Produit {product.id}: {str(e)}"
                errors.append(error_msg)
                logger.error(f"[BackgroundSync] Erreur: {error_msg}")
                self.db.session.rollback()
                continue
        
        duration = time.time() - start_time
        
        result = {
            'success': True,
            'message': f'{synced} produits synchronisés, {failed} échecs',
            'synced': synced,
            'failed': failed,
            'total': len(products),
            'duration': f'{int(duration)}s',
            'errors': errors[:10]  # Limiter à 10 erreurs
        }
        
        logger.info(f"[BackgroundSync] Batch terminé: {result['message']} en {result['duration']}")
        
        return result
    
    def sync_single_product(self, product_id: int) -> Dict:
        """
        Synchroniser un produit spécifique
        
        Args:
            product_id: ID du produit
            
        Returns:
            Résultat de la synchronisation
        """
        from models.product import Product
        from services.cj_variant_sync_service import CjVariantSyncService
        
        try:
            product = Product.query.get(product_id)
            
            if not product or not product.cj_pid:
                return {
                    'success': False,
                    'message': 'Produit introuvable ou non CJ'
                }
            
            # Récupérer détails depuis CJ API
            product_data = self.cj_api.get_product_details(product.cj_pid)
            
            if not product_data or 'data' not in product_data:
                return {
                    'success': False,
                    'message': 'Impossible de récupérer les données CJ'
                }
            
            data = product_data['data']
            
            # Détecter changements
            changes = {}
            old_stock = product.stock
            new_stock = int(data.get('productStock', 0) or data.get('stockQuantity', 0) or 0)
            
            if old_stock != new_stock:
                changes['stock'] = {'old': old_stock, 'new': new_stock}
            
            old_price = product.price
            new_price = float(data.get('sellPrice', 0) or 0)
            
            if old_price != new_price:
                changes['price'] = {'old': old_price, 'new': new_price}
            
            # Mettre à jour
            product.stock = new_stock
            product.price = new_price
            product.compare_price = float(data.get('suggestSellPrice', 0) or 0)
            product.synced_at = datetime.now()
            
            # Synchroniser variantes
            variant_sync_service = CjVariantSyncService(self.cj_api)
            
            if product.variants.count() > 0:
                try:
                    result = variant_sync_service.sync_product_variants(product.id)
                    if result['success']:
                        product.update_stock_from_variants()
                        changes['variants'] = result.get('total_variants', 0)
                except Exception as e:
                    logger.error(f"[BackgroundSync] Erreur sync variantes: {e}")
            
            self.db.session.commit()
            
            return {
                'success': True,
                'message': 'Produit synchronisé',
                'changes': changes,
                'product': {
                    'id': product.id,
                    'name': product.name,
                    'stock': product.stock,
                    'price': product.price
                }
            }
            
        except Exception as e:
            logger.error(f"[BackgroundSync] Erreur sync_single_product: {e}")
            self.db.session.rollback()
            return {
                'success': False,
                'message': str(e)
            }
    
    def get_sync_stats(self) -> Dict:
        """
        Obtenir les statistiques de synchronisation
        
        Returns:
            Statistiques
        """
        from models.product import Product
        
        try:
            total_cj_products = Product.query.filter(
                Product.cj_pid.isnot(None)
            ).count()
            
            active_cj_products = Product.query.filter(
                Product.cj_pid.isnot(None),
                Product.is_active == True
            ).count()
            
            never_synced = Product.query.filter(
                Product.cj_pid.isnot(None),
                Product.synced_at.is_(None)
            ).count()
            
            # Produits synchronisés dans les dernières 24h
            yesterday = datetime.now() - timedelta(days=1)
            synced_24h = Product.query.filter(
                Product.cj_pid.isnot(None),
                Product.synced_at >= yesterday
            ).count()
            
            # Produits avec stock bas
            low_stock = Product.query.filter(
                Product.cj_pid.isnot(None),
                Product.is_active == True,
                Product.stock < 10,
                Product.stock > 0
            ).count()
            
            # Produits en rupture
            out_of_stock = Product.query.filter(
                Product.cj_pid.isnot(None),
                Product.is_active == True,
                Product.stock == 0
            ).count()
            
            return {
                'total_cj_products': total_cj_products,
                'active_cj_products': active_cj_products,
                'never_synced': never_synced,
                'synced_last_24h': synced_24h,
                'low_stock': low_stock,
                'out_of_stock': out_of_stock,
                'can_sync': self.can_make_request(),
                'wait_time': self.get_wait_time()
            }
            
        except Exception as e:
            logger.error(f"[BackgroundSync] Erreur get_sync_stats: {e}")
            return {}
