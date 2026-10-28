"""
Service de synchronisation CJ Dropshipping
Inspiré de TonyAlpha80/src/Services/CjSyncService.php
Gère la synchronisation des catégories, produits et variantes entre CJ et la BDD locale
"""
import json
from typing import List, Dict, Optional
from datetime import datetime
from extensions import db
from models.category import Category
from models.product import Product
from models.product_variant import ProductVariant
from services.api_providers.cj_dropshipping_optimized import CJDropshippingApiOptimized
from services.pricing_service import PricingService
from sqlalchemy import func
import logging

logger = logging.getLogger(__name__)


class CjSyncService:
    """
    Service de synchronisation CJ Dropshipping
    """
    
    def __init__(self, cj_api: CJDropshippingApiOptimized):
        """Initialiser le service avec l'API CJ"""
        self.cj_api = cj_api
        self.pricing_service = PricingService()
    
    def _generate_unique_slug(self, base_name: str, cj_category_id: str) -> str:
        """Générer un slug unique pour une catégorie"""
        from slugify import slugify
        
        base_slug = slugify(base_name)
        
        # Vérifier si le slug existe déjà (tous les slugs, pas seulement CJ)
        existing = Category.query.filter_by(slug=base_slug).first()
        
        # Si le slug n'existe pas, ou s'il appartient à cette catégorie CJ, l'utiliser
        if not existing or existing.cj_category_id == cj_category_id:
            return base_slug
        
        # Si le slug existe et appartient à une autre catégorie, ajouter un suffixe
        # Utiliser les 8 premiers caractères du cj_category_id comme suffixe
        suffix = cj_category_id[:8].lower()
        unique_slug = f"{base_slug}-{suffix}"
        
        # Vérifier que ce slug unique n'existe pas non plus
        counter = 1
        final_slug = unique_slug
        while Category.query.filter_by(slug=final_slug).first():
            final_slug = f"{unique_slug}-{counter}"
            counter += 1
        
        return final_slug
    
    def sync_categories(self) -> Dict:
        """
        Synchroniser toutes les catégories CJ vers la BDD
        Retourne: {'success': bool, 'synced': int, 'total': int, 'errors': list}
        """
        try:
            logger.info("[CjSync] Début synchronisation catégories")
            
            # Récupérer les catégories depuis l'API CJ
            categories = self.cj_api.get_categories()
            
            if not categories:
                return {
                    'success': False,
                    'message': 'Aucune catégorie récupérée depuis CJ',
                    'synced': 0,
                    'total': 0,
                    'errors': []
                }
            
            synced = 0
            errors = []
            
            for category_data in categories:
                try:
                    self._sync_category(category_data)
                    db.session.commit()  # Commit après chaque catégorie
                    synced += 1
                except Exception as e:
                    db.session.rollback()  # Rollback en cas d'erreur
                    logger.error(f"[CjSync] Erreur sync catégorie {category_data.get('name')}: {e}")
                    errors.append({
                        'category': category_data.get('name', 'Unknown'),
                        'error': str(e)
                    })
            
            logger.info(f"[CjSync] {synced}/{len(categories)} catégories synchronisées")
            
            return {
                'success': True,
                'message': f"{synced} catégories synchronisées",
                'synced': synced,
                'total': len(categories),
                'errors': errors
            }
            
        except Exception as e:
            logger.error(f"[CjSync] Erreur sync_categories: {e}")
            db.session.rollback()
            return {
                'success': False,
                'message': str(e),
                'synced': 0,
                'total': 0,
                'errors': []
            }
    
    def _sync_category(self, category_data: Dict) -> None:
        """Synchroniser une catégorie CJ vers la BDD"""
        cj_id = category_data.get('cj_category_id')
        
        if not cj_id:
            raise ValueError("Catégorie sans cj_category_id")
        
        # Chercher si la catégorie existe déjà
        category = Category.query.filter_by(cj_category_id=cj_id).first()
        
        if category:
            # Mettre à jour
            category.name = category_data.get('name', category.name)
            category.name_fr = category_data.get('name_fr')
            category.level = category_data.get('level', 1)
            category.product_count = category_data.get('product_count', 0)
            category.last_sync = datetime.utcnow()
        else:
            # Créer nouvelle catégorie avec slug unique
            unique_slug = self._generate_unique_slug(
                category_data.get('name', ''),
                cj_id
            )
            
            category = Category(
                name=category_data.get('name', ''),
                slug=unique_slug,
                cj_category_id=cj_id,
                name_fr=category_data.get('name_fr'),
                level=category_data.get('level', 1),
                product_count=category_data.get('product_count', 0),
                visible=False,  # Non visible sur le site (uniquement pour admin)
                is_active=True,
                last_sync=datetime.utcnow()
            )
            db.session.add(category)
        
        # Gérer la hiérarchie parent/enfant
        parent_cj_id = category_data.get('parent_id')
        if parent_cj_id:
            parent = Category.query.filter_by(cj_category_id=parent_cj_id).first()
            if parent:
                category.parent_id = parent.id
    
    def sync_products(self, category_id: Optional[str] = None, limit: int = 100) -> Dict:
        """
        Synchroniser les produits d'une catégorie CJ vers la BDD
        Args:
            category_id: ID catégorie CJ (None = tous)
            limit: Nombre max de produits à synchroniser
        """
        try:
            logger.info(f"[CjSync] Début sync produits (catégorie: {category_id}, limit: {limit})")
            
            synced = 0
            errors = []
            page = 1
            
            while synced < limit:
                # Récupérer produits depuis l'API CJ
                filters = {'categoryId': category_id} if category_id else {}
                result = self.cj_api.get_products(
                    page=page,
                    page_size=min(20, limit - synced),
                    filters=filters
                )
                
                products = result.get('products', [])
                
                if not products:
                    break
                
                # Synchroniser chaque produit
                for product_data in products:
                    if synced >= limit:
                        break
                    
                    try:
                        self._sync_product(product_data)
                        db.session.commit()  # Commit après chaque produit
                        synced += 1
                    except Exception as e:
                        db.session.rollback()  # Rollback en cas d'erreur
                        logger.error(f"[CjSync] Erreur sync produit {product_data.get('pid')}: {e}")
                        errors.append({
                            'product': product_data.get('name', 'Unknown'),
                            'error': str(e)
                        })
                
                page += 1
                
                # Arrêter si c'était la dernière page
                if page > result.get('total_pages', 1):
                    break
            
            logger.info(f"[CjSync] {synced} produits synchronisés")
            
            # Mettre à jour les compteurs de produits pour toutes les catégories
            self._update_category_counts()
            
            return {
                'success': True,
                'message': f"{synced} produits synchronisés",
                'synced': synced,
                'errors': errors
            }
            
        except Exception as e:
            logger.error(f"[CjSync] Erreur sync_products: {e}")
            db.session.rollback()
            return {
                'success': False,
                'message': str(e),
                'synced': 0,
                'errors': []
            }
    
    def _sync_product(self, product_data: Dict) -> None:
        """Synchroniser un produit CJ vers la BDD"""
        import json
        
        pid = product_data.get('pid')
        sku = product_data.get('sku')
        
        if not pid:
            raise ValueError("Produit sans PID")
        
        # Chercher si le produit existe déjà (par cj_pid ou SKU)
        product = Product.query.filter_by(cj_pid=pid).first()
        
        if not product and sku:
            # Vérifier aussi par SKU pour éviter les doublons
            product = Product.query.filter_by(sku=sku).first()
        
        # Trouver la catégorie
        category = None
        if product_data.get('category_id'):
            category = Category.query.filter_by(
                cj_category_id=product_data['category_id']
            ).first()
        
        if not category:
            # Utiliser une catégorie par défaut
            category = Category.query.filter_by(level=1).first()
            if not category:
                raise ValueError("Aucune catégorie disponible")
        
        # Récupérer les prix CJ
        cj_sell_price = product_data.get('price', 0)  # Prix d'achat CJ
        cj_suggested_price = product_data.get('suggested_price')  # Prix suggéré CJ
        
        if product:
            # Mettre à jour produit existant
            product.name = product_data.get('name', product.name)
            product.description = product_data.get('description', product.description)
            product.stock = product_data.get('stock', 0)
            product.sku = product_data.get('sku', product.sku)
            product.product_weight = product_data.get('weight')
            product.material = product_data.get('material')
            product.synced_at = datetime.utcnow()
            product.cj_last_sync = datetime.utcnow()
            
            # Sauvegarder les données brutes CJ pour audit
            product.cj_raw_data = json.dumps(product_data, ensure_ascii=False)
            
            # Activer et publier automatiquement
            product.is_active = True
            product.published = True
            
            # Calculer les prix avec PricingService
            product = self.pricing_service.update_product_pricing(
                product, 
                cj_sell_price, 
                cj_suggested_price
            )
            
            # Mettre à jour images
            images = product_data.get('images', [])
            if images:
                product.image_url = images[0]
                product.set_images_list(images[1:] if len(images) > 1 else [])
        else:
            # Créer nouveau produit avec slug unique
            from slugify import slugify
            
            images = product_data.get('images', [])
            base_slug = slugify(product_data.get('name', ''))
            
            # Générer un slug unique si nécessaire
            unique_slug = base_slug
            counter = 1
            while Product.query.filter_by(slug=unique_slug).first():
                unique_slug = f"{base_slug}-{counter}"
                counter += 1
            
            # Calculer le prix de vente avec marge
            markup = self.pricing_service.get_markup_for_category(category.name)
            selling_price = self.pricing_service.calculate_selling_price(cj_sell_price, markup)
            
            product = Product(
                name=product_data.get('name', ''),
                slug=unique_slug,
                cj_pid=pid,
                sku=sku or f"CJ-{pid[:10]}",
                description=product_data.get('description', ''),
                cost_price=cj_sell_price,  # Prix CJ
                price=selling_price,  # Prix calculé avec marge
                suggested_price=cj_suggested_price,
                compare_price=cj_suggested_price,  # Prix barré
                stock=product_data.get('stock', 0),
                image_url=images[0] if images else None,
                category_id=category.id,
                product_weight=product_data.get('weight'),
                material=product_data.get('material'),
                is_active=True,  # Actif par défaut
                published=True,  # Publié automatiquement
                synced_at=datetime.utcnow(),
                cj_last_sync=datetime.utcnow(),
                cj_raw_data=json.dumps(product_data, ensure_ascii=False)  # Données brutes pour audit
            )
            
            if len(images) > 1:
                product.set_images_list(images[1:])
            
            db.session.add(product)
        
        # Forcer un flush pour obtenir l'ID du produit
        db.session.flush()
        
        # Synchroniser les variantes
        variants = product_data.get('variants', [])
        if variants:
            self._sync_variants(product.id, variants)
    
    def _sync_variants(self, product_id: int, variants: List[Dict]) -> None:
        """Synchroniser les variantes d'un produit"""
        # Supprimer les anciennes variantes
        ProductVariant.query.filter_by(product_id=product_id).delete()
        
        # Ajouter les nouvelles variantes
        for variant_data in variants:
            vid = variant_data.get('vid')
            if not vid:
                continue
            
            # Extraire couleur et taille depuis variant_key (ex: "White-S")
            variant_key = variant_data.get('key', '')
            parts = variant_key.split('-')
            color = parts[0] if len(parts) > 0 else None
            size = parts[1] if len(parts) > 1 else None
            
            variant = ProductVariant(
                product_id=product_id,
                cj_vid=vid,
                variant_key=variant_key,
                color=color,
                size=size,
                price=variant_data.get('price'),
                suggested_price=variant_data.get('suggested_price'),
                stock=variant_data.get('stock', 0),
                image_url=variant_data.get('image'),
                weight=variant_data.get('weight'),
                sku=variant_data.get('sku'),
                active=True,
                cj_raw_data=json.dumps(variant_data, ensure_ascii=False)  # Données brutes pour audit
            )
            db.session.add(variant)
    
    def sync_stock(self) -> Dict:
        """Synchroniser le stock de tous les produits CJ actifs"""
        try:
            logger.info("[CjSync] Début sync stock")
            
            # Récupérer tous les produits CJ actifs
            products = Product.query.filter(
                Product.cj_pid.isnot(None),
                Product.is_active == True
            ).all()
            
            updated = 0
            errors = []
            
            for product in products:
                try:
                    # Récupérer les détails depuis l'API
                    details = self.cj_api.get_product_details(product.cj_pid)
                    
                    if details:
                        product.stock = details.get('stock', 0)
                        product.synced_at = datetime.utcnow()
                        updated += 1
                        
                except Exception as e:
                    logger.error(f"[CjSync] Erreur sync stock {product.cj_pid}: {e}")
                    errors.append({
                        'pid': product.cj_pid,
                        'error': str(e)
                    })
            
            db.session.commit()
            
            logger.info(f"[CjSync] {updated} stocks mis à jour")
            
            return {
                'success': True,
                'message': f"{updated} stocks mis à jour",
                'updated': updated,
                'total': len(products),
                'errors': errors
            }
            
        except Exception as e:
            logger.error(f"[CjSync] Erreur sync_stock: {e}")
            db.session.rollback()
            return {
                'success': False,
                'message': str(e),
                'updated': 0,
                'errors': []
            }
    
    def get_stats(self) -> Dict:
        """Obtenir les statistiques de synchronisation"""
        try:
            stats = {}
            
            # Statistiques produits
            stats['products'] = {
                'total': Product.query.filter(Product.cj_pid.isnot(None)).count(),
                'synced': Product.query.filter(Product.synced_at.isnot(None)).count(),
                'published': Product.query.filter(Product.published == True).count(),
                'in_stock': Product.query.filter(
                    Product.cj_pid.isnot(None),
                    Product.stock > 0
                ).count()
            }
            
            # Statistiques variantes
            stats['variants'] = {
                'total': ProductVariant.query.count(),
                'active': ProductVariant.query.filter_by(active=True).count()
            }
            
            # Statistiques catégories
            stats['categories'] = {
                'total': Category.query.filter(Category.cj_category_id.isnot(None)).count(),
                'level_1': Category.query.filter_by(level=1).count(),
                'level_2': Category.query.filter_by(level=2).count(),
                'level_3': Category.query.filter_by(level=3).count(),
                'visible': Category.query.filter_by(visible=True).count()
            }
            
            # Dernière synchronisation
            last_sync = db.session.query(func.max(Product.synced_at)).scalar()
            stats['last_sync'] = last_sync.isoformat() if last_sync else None
            
            return stats
            
        except Exception as e:
            logger.error(f"[CjSync] Erreur get_stats: {e}")
            return {
                'products': {'total': 0, 'synced': 0, 'published': 0, 'in_stock': 0},
                'variants': {'total': 0, 'active': 0},
                'categories': {'total': 0, 'level_1': 0, 'level_2': 0, 'level_3': 0, 'visible': 0},
                'last_sync': None
            }
    
    def enrich_product(self, pid: str) -> Dict:
        """
        Enrichir un produit avec toutes les données CJ
        (détails, variantes, avis clients)
        """
        try:
            logger.info(f"[CjSync] Enrichissement produit {pid}")
            
            # Récupérer détails complets
            details = self.cj_api.get_product_details(pid)
            if not details:
                return {'success': False, 'error': 'Produit non trouvé'}
            
            # Récupérer avis clients
            comments = self.cj_api.get_product_comments(pid, page=1, page_size=50)
            
            # Calculer note moyenne
            if comments:
                total_rating = sum(c.get('rating', 0) for c in comments)
                avg_rating = total_rating / len(comments) if comments else 0
            else:
                avg_rating = 0
            
            # Mettre à jour le produit en BDD
            product = Product.query.filter_by(cj_pid=pid).first()
            if product:
                product.rating_average = avg_rating
                product.rating_count = len(comments)
                db.session.commit()
            
            return {
                'success': True,
                'details': details,
                'comments': comments,
                'rating': avg_rating,
                'review_count': len(comments)
            }
            
        except Exception as e:
            logger.error(f"[CjSync] Erreur enrich_product: {e}")
            return {'success': False, 'error': str(e)}

    def _update_category_counts(self):
        """Mettre à jour les compteurs de produits pour toutes les catégories CJ"""
        try:
            logger.info("[CjSync] Mise à jour des compteurs de catégories")
            
            # Récupérer toutes les catégories CJ
            categories = Category.query.filter(
                Category.cj_category_id.isnot(None)
            ).all()
            
            for category in categories:
                # Compter les produits directs de cette catégorie
                direct_count = Product.query.filter(
                    Product.category_id == category.id,
                    Product.cj_pid.isnot(None),
                    Product.published == True
                ).count()
                
                # Pour les catégories de niveau 1 et 2, inclure les sous-catégories
                total_count = direct_count
                
                if category.level == 1:
                    # Ajouter produits des catégories niveau 2
                    level2_cats = Category.query.filter_by(parent_id=category.id).all()
                    for cat2 in level2_cats:
                        total_count += Product.query.filter(
                            Product.category_id == cat2.id,
                            Product.cj_pid.isnot(None),
                            Product.published == True
                        ).count()
                        
                        # Ajouter produits des catégories niveau 3
                        level3_cats = Category.query.filter_by(parent_id=cat2.id).all()
                        for cat3 in level3_cats:
                            total_count += Product.query.filter(
                                Product.category_id == cat3.id,
                                Product.cj_pid.isnot(None),
                                Product.published == True
                            ).count()
                
                elif category.level == 2:
                    # Ajouter produits des catégories niveau 3
                    level3_cats = Category.query.filter_by(parent_id=category.id).all()
                    for cat3 in level3_cats:
                        total_count += Product.query.filter(
                            Product.category_id == cat3.id,
                            Product.cj_pid.isnot(None),
                            Product.published == True
                        ).count()
                
                # Mettre à jour le compteur
                category.product_count = total_count
            
            db.session.commit()
            logger.info("[CjSync] Compteurs de catégories mis à jour")
            
        except Exception as e:
            logger.error(f"[CjSync] Erreur _update_category_counts: {e}")
            db.session.rollback()
