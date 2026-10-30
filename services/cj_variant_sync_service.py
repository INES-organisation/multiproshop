"""
Service de synchronisation des variantes depuis CJ Dropshipping API
"""
from models.product import Product
from models.product_variant import ProductVariant
from extensions import db
import logging

logger = logging.getLogger(__name__)


class CjVariantSyncService:
    """Service pour synchroniser les variantes depuis CJ API"""
    
    def __init__(self, cj_api):
        self.cj_api = cj_api
    
    def sync_product_variants(self, product_id):
        """
        Synchroniser les variantes d'un produit depuis CJ API
        
        Args:
            product_id: ID du produit local
            
        Returns:
            dict: Résultat de la synchronisation
        """
        try:
            product = Product.query.get(product_id)
            
            if not product or not product.cj_pid:
                return {
                    'success': False,
                    'message': 'Produit CJ introuvable'
                }
            
            logger.info(f"Synchronisation variantes pour produit {product.cj_pid}")
            
            # Récupérer les détails du produit depuis CJ API
            product_data = self.cj_api.get_product_details(product.cj_pid)
            
            if not product_data:
                return {
                    'success': False,
                    'message': 'Impossible de récupérer les données CJ'
                }
            
            # Extraire les variantes depuis les données CJ
            variants_data = self._extract_variants_from_cj_data(product_data)
            
            if not variants_data:
                logger.info(f"Aucune variante trouvée pour {product.cj_pid}")
                return {
                    'success': True,
                    'message': 'Aucune variante disponible',
                    'variants_created': 0,
                    'variants_updated': 0
                }
            
            # Synchroniser les variantes
            created = 0
            updated = 0
            
            for variant_data in variants_data:
                result = self._sync_single_variant(product, variant_data)
                if result == 'created':
                    created += 1
                elif result == 'updated':
                    updated += 1
            
            db.session.commit()
            
            logger.info(f"Synchronisation terminée: {created} créées, {updated} mises à jour")
            
            return {
                'success': True,
                'message': f'{created} variantes créées, {updated} mises à jour',
                'variants_created': created,
                'variants_updated': updated,
                'total_variants': created + updated
            }
            
        except Exception as e:
            logger.error(f"Erreur sync variantes: {e}")
            db.session.rollback()
            return {
                'success': False,
                'message': str(e)
            }
    
    def _extract_variants_from_cj_data(self, product_data):
        """
        Extraire les variantes depuis les données CJ (brutes ou formatées)
        
        Supporte deux formats:
        1. Données brutes CJ: variantSellPrice, variantKey, inventories[].totalInventory
        2. Données formatées par _format_product: vid, key, stock, price, image
        
        Args:
            product_data: Données produit depuis CJ API
            
        Returns:
            list: Liste des variantes
        """
        variants = []
        
        if not isinstance(product_data, dict):
            return variants
        
        # Essayer différentes structures possibles
        variant_list = (
            product_data.get('data', {}).get('variants') if isinstance(product_data.get('data'), dict) else None
        ) or (
            product_data.get('data', {}).get('variantList') if isinstance(product_data.get('data'), dict) else None
        ) or (
            product_data.get('variants')
        ) or (
            product_data.get('variantList')
        ) or []
        
        if not variant_list:
            return variants
        
        for v in variant_list:
            # Extraire le nom et la clé de variante (brut ou formaté)
            variant_name = v.get('variantNameEn') or v.get('variantName') or ''
            variant_key = v.get('variantKey') or v.get('key') or v.get('variantSku') or ''
            
            # Parser couleur et taille
            color = v.get('color') or None
            size = v.get('size') or v.get('variantSize') or None
            
            if not color and not size and variant_name:
                parts = variant_name.split('-') if '-' in variant_name else variant_name.split()
                if len(parts) >= 2:
                    color = parts[0].strip()
                    size = parts[1].strip()
                elif len(parts) == 1:
                    color = parts[0].strip()
            
            if not color and variant_key:
                color = variant_key.split('-')[0] if '-' in variant_key else variant_key
            
            # Extraire le stock depuis inventories (structure CJ API v2)
            variant_stock = 0
            inventories = v.get('inventories')
            if inventories and isinstance(inventories, list):
                for inv in inventories:
                    variant_stock += int(inv.get('totalInventory', 0) or 0)
            
            # Fallback: stock déjà calculé par _format_product ou clés brutes
            if variant_stock == 0:
                variant_stock = int(
                    v.get('stock', 0) or 
                    v.get('variantStock', 0) or 
                    v.get('variantQuantity', 0) or 
                    v.get('inventoryNum', 0) or 
                    v.get('quantity', 0) or 
                    0
                )
            
            # Extraire le prix (brut ou formaté)
            price = float(
                v.get('variantSellPrice', 0) or 
                v.get('price', 0) or 
                v.get('sellPrice', 0) or 
                0
            )
            
            variant = {
                'cj_vid': v.get('vid') or v.get('variantId') or v.get('id'),
                'variant_key': variant_key or variant_name,
                'color': color,
                'size': size,
                'price': price,
                'stock': variant_stock,
                'image_url': v.get('variantImage') or v.get('image') or v.get('variantImg'),
                'weight': int(v.get('variantWeight', 0) or v.get('weight', 0) or 0),
                'sku': v.get('variantSku') or v.get('sku') or variant_key,
            }
            
            # Valider que la variante a au moins un ID
            if variant['cj_vid']:
                variants.append(variant)
        
        return variants
    
    def _sync_single_variant(self, product, variant_data):
        """
        Synchroniser une seule variante
        
        Args:
            product: Instance Product
            variant_data: Données de la variante
            
        Returns:
            str: 'created', 'updated' ou None
        """
        cj_vid = variant_data.get('cj_vid')
        
        if not cj_vid:
            return None
        
        # Chercher si la variante existe déjà
        variant = ProductVariant.query.filter_by(
            product_id=product.id,
            cj_vid=cj_vid
        ).first()
        
        if variant:
            # Mise à jour
            variant.variant_key = variant_data.get('variant_key') or variant.variant_key
            variant.color = variant_data.get('color') or variant.color
            variant.size = variant_data.get('size') or variant.size
            # variant_data['price'] est le coût CJ : on ne l'écrit pas comme prix de vente
            variant.stock = variant_data.get('stock', 0)
            variant.image_url = variant_data.get('image_url') or variant.image_url
            variant.weight = variant_data.get('weight') or variant.weight
            variant.sku = variant_data.get('sku') or variant.sku
            variant.active = True
            
            return 'updated'
        else:
            # Création
            variant = ProductVariant(
                product_id=product.id,
                cj_vid=cj_vid,
                variant_key=variant_data.get('variant_key'),
                color=variant_data.get('color'),
                size=variant_data.get('size'),
                price=None,  # coût CJ dans variant_data : le prix de vente du produit s'applique
                suggested_price=product.compare_price,
                stock=variant_data.get('stock', 0),
                image_url=variant_data.get('image_url') or product.image_url,
                weight=variant_data.get('weight'),
                sku=variant_data.get('sku'),
                active=True
            )
            
            db.session.add(variant)
            return 'created'
    
    def sync_variant_stock(self, variant_id):
        """
        Synchroniser le stock d'une variante spécifique depuis CJ
        
        Args:
            variant_id: ID de la variante locale
            
        Returns:
            dict: Résultat de la synchronisation
        """
        try:
            variant = ProductVariant.query.get(variant_id)
            
            if not variant or not variant.cj_vid:
                return {
                    'success': False,
                    'message': 'Variante introuvable'
                }
            
            product = variant.product
            
            if not product or not product.cj_pid:
                return {
                    'success': False,
                    'message': 'Produit CJ introuvable'
                }
            
            # Récupérer les données du produit
            product_data = self.cj_api.get_product_details(product.cj_pid)
            
            if not product_data:
                return {
                    'success': False,
                    'message': 'Impossible de récupérer les données CJ'
                }
            
            # Trouver la variante dans les données
            variants_data = self._extract_variants_from_cj_data(product_data)
            
            for v_data in variants_data:
                if v_data.get('cj_vid') == variant.cj_vid:
                    old_stock = variant.stock
                    new_stock = v_data.get('stock', 0)
                    
                    variant.stock = new_stock
                    db.session.commit()
                    
                    return {
                        'success': True,
                        'message': f'Stock mis à jour: {old_stock} → {new_stock}',
                        'old_stock': old_stock,
                        'new_stock': new_stock
                    }
            
            return {
                'success': False,
                'message': 'Variante non trouvée dans les données CJ'
            }
            
        except Exception as e:
            logger.error(f"Erreur sync stock variante: {e}")
            db.session.rollback()
            return {
                'success': False,
                'message': str(e)
            }
    
    def sync_all_variants_stock(self, product_id):
        """
        Synchroniser le stock de toutes les variantes d'un produit
        
        Args:
            product_id: ID du produit local
            
        Returns:
            dict: Résultat de la synchronisation
        """
        try:
            product = Product.query.get(product_id)
            
            if not product or not product.cj_pid:
                return {
                    'success': False,
                    'message': 'Produit CJ introuvable'
                }
            
            # Récupérer toutes les variantes locales
            variants = ProductVariant.query.filter_by(product_id=product_id).all()
            
            if not variants:
                return {
                    'success': True,
                    'message': 'Aucune variante à synchroniser',
                    'updated': 0
                }
            
            # Récupérer les données CJ
            product_data = self.cj_api.get_product_details(product.cj_pid)
            
            if not product_data:
                return {
                    'success': False,
                    'message': 'Impossible de récupérer les données CJ'
                }
            
            variants_data = self._extract_variants_from_cj_data(product_data)
            
            # Créer un mapping cj_vid -> stock
            stock_map = {v['cj_vid']: v['stock'] for v in variants_data if v.get('cj_vid')}
            
            updated = 0
            for variant in variants:
                if variant.cj_vid in stock_map:
                    new_stock = stock_map[variant.cj_vid]
                    if variant.stock != new_stock:
                        variant.stock = new_stock
                        updated += 1
            
            db.session.commit()
            
            return {
                'success': True,
                'message': f'{updated} variantes mises à jour',
                'updated': updated,
                'total': len(variants)
            }
            
        except Exception as e:
            logger.error(f"Erreur sync stock toutes variantes: {e}")
            db.session.rollback()
            return {
                'success': False,
                'message': str(e)
            }
    
    def get_variant_stock_status(self, variant_id):
        """
        Obtenir le statut du stock d'une variante en temps réel
        
        Args:
            variant_id: ID de la variante
            
        Returns:
            dict: Statut du stock
        """
        try:
            variant = ProductVariant.query.get(variant_id)
            
            if not variant:
                return {
                    'success': False,
                    'message': 'Variante introuvable'
                }
            
            return {
                'success': True,
                'variant_id': variant.id,
                'cj_vid': variant.cj_vid,
                'stock': variant.stock,
                'is_in_stock': variant.stock > 0,
                'price': float(variant.price) if variant.price else 0,
                'active': variant.active
            }
            
        except Exception as e:
            logger.error(f"Erreur get stock status: {e}")
            return {
                'success': False,
                'message': str(e)
            }
