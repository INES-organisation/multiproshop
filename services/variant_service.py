"""
Service de gestion des variantes de produits CJ
Gère la logique métier pour les couleurs, tailles et options de produits
"""
from typing import List, Dict, Optional, Tuple
from models.product import Product
from models.product_variant import ProductVariant
from extensions import db
import logging

logger = logging.getLogger(__name__)


class VariantService:
    """Service pour gérer les variantes de produits"""
    
    def get_product_variants(self, product_id: int) -> List[Dict]:
        """
        Récupérer toutes les variantes d'un produit
        
        Args:
            product_id: ID du produit
            
        Returns:
            Liste des variantes avec leurs informations
        """
        try:
            variants = ProductVariant.query.filter_by(
                product_id=product_id,
                active=True
            ).all()
            
            return [self._format_variant(v) for v in variants]
            
        except Exception as e:
            logger.error(f"[VariantService] Erreur get_product_variants: {e}")
            return []
    
    def get_variant_by_id(self, variant_id: int) -> Optional[Dict]:
        """
        Récupérer une variante par son ID
        
        Args:
            variant_id: ID de la variante
            
        Returns:
            Informations de la variante ou None
        """
        try:
            variant = ProductVariant.query.get(variant_id)
            if variant and variant.active:
                return self._format_variant(variant)
            return None
            
        except Exception as e:
            logger.error(f"[VariantService] Erreur get_variant_by_id: {e}")
            return None
    
    def get_variant_by_cj_vid(self, cj_vid: str) -> Optional[Dict]:
        """
        Récupérer une variante par son ID CJ
        
        Args:
            cj_vid: ID CJ de la variante
            
        Returns:
            Informations de la variante ou None
        """
        try:
            variant = ProductVariant.query.filter_by(cj_vid=cj_vid).first()
            if variant and variant.active:
                return self._format_variant(variant)
            return None
            
        except Exception as e:
            logger.error(f"[VariantService] Erreur get_variant_by_cj_vid: {e}")
            return None
    
    def get_variant_by_options(self, product_id: int, color: Optional[str] = None, 
                               size: Optional[str] = None) -> Optional[Dict]:
        """
        Récupérer une variante par ses options (couleur, taille)
        
        Args:
            product_id: ID du produit
            color: Couleur recherchée
            size: Taille recherchée
            
        Returns:
            Informations de la variante ou None
        """
        try:
            query = ProductVariant.query.filter_by(
                product_id=product_id,
                active=True
            )
            
            if color:
                query = query.filter_by(color=color)
            if size:
                query = query.filter_by(size=size)
            
            variant = query.first()
            if variant:
                return self._format_variant(variant)
            return None
            
        except Exception as e:
            logger.error(f"[VariantService] Erreur get_variant_by_options: {e}")
            return None
    
    def get_available_colors(self, product_id: int) -> List[str]:
        """
        Récupérer toutes les couleurs disponibles pour un produit
        
        Args:
            product_id: ID du produit
            
        Returns:
            Liste des couleurs uniques
        """
        try:
            variants = ProductVariant.query.filter_by(
                product_id=product_id,
                active=True
            ).filter(ProductVariant.color.isnot(None)).all()
            
            colors = list(set([v.color for v in variants if v.color]))
            return sorted(colors)
            
        except Exception as e:
            logger.error(f"[VariantService] Erreur get_available_colors: {e}")
            return []
    
    def get_available_sizes(self, product_id: int, color: Optional[str] = None) -> List[str]:
        """
        Récupérer toutes les tailles disponibles pour un produit
        Optionnellement filtré par couleur
        
        Args:
            product_id: ID du produit
            color: Couleur pour filtrer les tailles
            
        Returns:
            Liste des tailles uniques
        """
        try:
            query = ProductVariant.query.filter_by(
                product_id=product_id,
                active=True
            ).filter(ProductVariant.size.isnot(None))
            
            if color:
                query = query.filter_by(color=color)
            
            variants = query.all()
            sizes = list(set([v.size for v in variants if v.size]))
            return sorted(sizes)
            
        except Exception as e:
            logger.error(f"[VariantService] Erreur get_available_sizes: {e}")
            return []
    
    def get_variant_stock(self, variant_id: int) -> int:
        """
        Récupérer le stock d'une variante
        
        Args:
            variant_id: ID de la variante
            
        Returns:
            Quantité en stock
        """
        try:
            variant = ProductVariant.query.get(variant_id)
            return variant.stock if variant else 0
            
        except Exception as e:
            logger.error(f"[VariantService] Erreur get_variant_stock: {e}")
            return 0
    
    def check_variant_availability(self, variant_id: int, quantity: int = 1) -> Tuple[bool, str]:
        """
        Vérifier la disponibilité d'une variante
        
        Args:
            variant_id: ID de la variante
            quantity: Quantité demandée
            
        Returns:
            Tuple (disponible, message)
        """
        try:
            variant = ProductVariant.query.get(variant_id)
            
            if not variant:
                return False, "Variante introuvable"
            
            if not variant.active:
                return False, "Variante non disponible"
            
            if variant.stock < quantity:
                return False, f"Stock insuffisant (disponible: {variant.stock})"
            
            return True, "Disponible"
            
        except Exception as e:
            logger.error(f"[VariantService] Erreur check_variant_availability: {e}")
            return False, "Erreur lors de la vérification"
    
    def reduce_variant_stock(self, variant_id: int, quantity: int) -> bool:
        """
        Réduire le stock d'une variante
        
        Args:
            variant_id: ID de la variante
            quantity: Quantité à déduire
            
        Returns:
            True si succès, False sinon
        """
        try:
            variant = ProductVariant.query.get(variant_id)
            
            if not variant:
                logger.error(f"[VariantService] Variante {variant_id} introuvable")
                return False
            
            if variant.stock < quantity:
                logger.error(f"[VariantService] Stock insuffisant pour variante {variant_id}")
                return False
            
            variant.stock -= quantity
            db.session.commit()
            
            logger.info(f"[VariantService] Stock réduit: variante {variant_id}, quantité {quantity}")
            return True
            
        except Exception as e:
            logger.error(f"[VariantService] Erreur reduce_variant_stock: {e}")
            db.session.rollback()
            return False
    
    def restore_variant_stock(self, variant_id: int, quantity: int) -> bool:
        """
        Restaurer le stock d'une variante (annulation commande)
        
        Args:
            variant_id: ID de la variante
            quantity: Quantité à restaurer
            
        Returns:
            True si succès, False sinon
        """
        try:
            variant = ProductVariant.query.get(variant_id)
            
            if not variant:
                logger.error(f"[VariantService] Variante {variant_id} introuvable")
                return False
            
            variant.stock += quantity
            db.session.commit()
            
            logger.info(f"[VariantService] Stock restauré: variante {variant_id}, quantité {quantity}")
            return True
            
        except Exception as e:
            logger.error(f"[VariantService] Erreur restore_variant_stock: {e}")
            db.session.rollback()
            return False
    
    def get_product_variants_summary(self, product_id: int) -> Dict:
        """
        Récupérer un résumé des variantes d'un produit
        
        Args:
            product_id: ID du produit
            
        Returns:
            Résumé avec options disponibles et statistiques
        """
        try:
            variants = ProductVariant.query.filter_by(
                product_id=product_id,
                active=True
            ).all()
            
            if not variants:
                return {
                    'has_variants': False,
                    'total_variants': 0,
                    'colors': [],
                    'sizes': [],
                    'total_stock': 0,
                    'price_range': None
                }
            
            colors = list(set([v.color for v in variants if v.color]))
            sizes = list(set([v.size for v in variants if v.size]))
            total_stock = sum([v.stock for v in variants])
            
            prices = [v.price for v in variants if v.price]
            price_range = None
            if prices:
                min_price = min(prices)
                max_price = max(prices)
                price_range = {
                    'min': min_price,
                    'max': max_price,
                    'same': min_price == max_price
                }
            
            return {
                'has_variants': True,
                'total_variants': len(variants),
                'colors': sorted(colors),
                'sizes': sorted(sizes),
                'total_stock': total_stock,
                'price_range': price_range,
                'variants': [self._format_variant(v) for v in variants]
            }
            
        except Exception as e:
            logger.error(f"[VariantService] Erreur get_product_variants_summary: {e}")
            return {
                'has_variants': False,
                'total_variants': 0,
                'colors': [],
                'sizes': [],
                'total_stock': 0,
                'price_range': None
            }
    
    def _format_variant(self, variant: ProductVariant) -> Dict:
        """
        Formater une variante pour l'API
        
        Args:
            variant: Instance ProductVariant
            
        Returns:
            Dictionnaire formaté
        """
        return {
            'id': variant.id,
            'cj_vid': variant.cj_vid,
            'variant_key': variant.variant_key,
            'color': variant.color,
            'size': variant.size,
            'price': variant.price,
            'suggested_price': variant.suggested_price,
            'stock': variant.stock,
            'image_url': variant.image_url,
            'weight': variant.weight,
            'sku': variant.sku,
            'active': variant.active,
            'display_name': variant.display_name,
            'is_in_stock': variant.is_in_stock
        }
