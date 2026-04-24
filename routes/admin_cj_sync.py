"""
Routes admin pour la synchronisation CJ Dropshipping
Inspiré de TonyAlpha80/src/Controllers/CjController.php
"""
from flask import Blueprint, jsonify, request, session
from flask_login import login_required
from services.cj_sync_service import CjSyncService
from services.api_providers.cj_dropshipping_optimized import CJDropshippingApiOptimized
from services.pricing_service import PricingService
from models.category import Category
from models.product import Product
from extensions import db
from config import Config
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('admin_cj_sync', __name__, url_prefix='/admin/api/cj')
pricing_service = PricingService()


def get_cj_api():
    """Obtenir une instance de l'API CJ"""
    return CJDropshippingApiOptimized(
        email=Config.CJ_EMAIL,
        password=Config.CJ_PASSWORD,
        dev_key=Config.CJ_DEV_KEY
    )


@bp.route('/sync/categories', methods=['POST'])
@login_required
def sync_categories():
    """
    Synchroniser les catégories CJ
    POST /admin/api/cj/sync/categories
    """
    try:
        logger.info("[Admin] Demande sync catégories CJ")
        
        cj_api = get_cj_api()
        sync_service = CjSyncService(cj_api)
        
        result = sync_service.sync_categories()
        
        return jsonify(result), 200 if result['success'] else 500
        
    except Exception as e:
        logger.error(f"[Admin] Erreur sync catégories: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@bp.route('/sync/products', methods=['POST'])
@login_required
def sync_products():
    """
    Synchroniser les produits CJ
    POST /admin/api/cj/sync/products
    Body: {category_id: str, limit: int}
    """
    try:
        data = request.get_json() or {}
        category_id = data.get('category_id')
        limit = data.get('limit', 100)
        
        logger.info(f"[Admin] Demande sync produits (cat: {category_id}, limit: {limit})")
        
        cj_api = get_cj_api()
        sync_service = CjSyncService(cj_api)
        
        result = sync_service.sync_products(category_id, limit)
        
        return jsonify(result), 200 if result['success'] else 500
        
    except Exception as e:
        logger.error(f"[Admin] Erreur sync produits: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@bp.route('/sync/stock', methods=['POST'])
@login_required
def sync_stock():
    """
    Synchroniser le stock des produits CJ
    POST /admin/api/cj/sync/stock
    """
    try:
        logger.info("[Admin] Demande sync stock CJ")
        
        cj_api = get_cj_api()
        sync_service = CjSyncService(cj_api)
        
        result = sync_service.sync_stock()
        
        return jsonify(result), 200 if result['success'] else 500
        
    except Exception as e:
        logger.error(f"[Admin] Erreur sync stock: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@bp.route('/stats', methods=['GET'])
@login_required
def get_stats():
    """
    Obtenir les statistiques de synchronisation CJ
    GET /admin/api/cj/stats
    """
    try:
        cj_api = get_cj_api()
        sync_service = CjSyncService(cj_api)
        
        stats = sync_service.get_stats()
        
        return jsonify({
            'success': True,
            'stats': stats
        }), 200
        
    except Exception as e:
        logger.error(f"[Admin] Erreur stats: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@bp.route('/enrich/<pid>', methods=['POST'])
@login_required
def enrich_product(pid):
    """
    Enrichir un produit avec toutes les données CJ et sauvegarder
    POST /admin/api/cj/enrich/<pid>
    Récupère: détails, description, images, poids, avis, variantes
    """
    try:
        from extensions import db
        from services.cj_variant_sync_service import CjVariantSyncService
        from datetime import datetime
        import json
        
        logger.info(f"[Admin] Demande enrichissement produit {pid}")
        
        cj_api = get_cj_api()
        sync_service = CjSyncService(cj_api)
        
        product = Product.query.filter_by(cj_pid=pid).first()
        if not product:
            return jsonify({'success': False, 'message': 'Produit introuvable en BDD'}), 404
        
        # 1. Récupérer détails complets (formatés par _format_product)
        details = cj_api.get_product_details(pid)
        enriched_fields = []
        
        if details:
            if details.get('name') and details['name'] != product.name:
                product.name = details['name']
                enriched_fields.append('nom')
            
            if details.get('description'):
                product.description = details['description']
                enriched_fields.append('description')
            
            if details.get('image'):
                img = details['image']
                # Parser si c'est un JSON array
                if isinstance(img, str) and img.strip().startswith('['):
                    try:
                        parsed = json.loads(img)
                        if isinstance(parsed, list) and parsed:
                            img = parsed[0]
                    except (json.JSONDecodeError, ValueError):
                        pass
                product.image_url = img
                enriched_fields.append('image')
            
            if details.get('images') and len(details['images']) > 0:
                # Parser chaque image si c'est un JSON array
                clean_imgs = []
                for im in details['images']:
                    if isinstance(im, str) and im.strip().startswith('['):
                        try:
                            parsed = json.loads(im)
                            if isinstance(parsed, list):
                                clean_imgs.extend(parsed)
                            else:
                                clean_imgs.append(im)
                        except (json.JSONDecodeError, ValueError):
                            clean_imgs.append(im)
                    else:
                        clean_imgs.append(im)
                product.images = json.dumps(clean_imgs)
                enriched_fields.append(f"images ({len(clean_imgs)})")
            
            if details.get('weight'):
                try:
                    product.weight = float(details['weight'])
                    enriched_fields.append('poids')
                except (ValueError, TypeError):
                    pass
            
            if details.get('material'):
                product.material = details['material']
                enriched_fields.append('matériau')
            
            if details.get('suggested_price'):
                product.suggested_price = details['suggested_price']
            
            if details.get('price') and not product.cost_price:
                product.cost_price = details['price']
            
            # Sauvegarder les données brutes pour audit
            if details.get('raw_data'):
                product.cj_raw_data = json.dumps(details['raw_data'], default=str)
        
        # 2. Récupérer avis clients
        result = sync_service.enrich_product(pid)
        if result.get('success'):
            if result.get('rating'):
                product.rating_average = result['rating']
                enriched_fields.append('note')
            if result.get('review_count', 0) > 0:
                product.rating_count = result['review_count']
                enriched_fields.append(f"avis ({result['review_count']})")
        
        # 3. Synchroniser les variantes
        try:
            variant_sync = CjVariantSyncService(cj_api)
            var_result = variant_sync.sync_product_variants(product.id)
            if var_result.get('success') and var_result.get('total_variants', 0) > 0:
                enriched_fields.append(f"variantes ({var_result['total_variants']})")
                product.update_stock_from_variants()
        except Exception as e:
            logger.warning(f"[Admin] Sync variantes échouée: {e}")
        
        # Mettre à jour la date de sync
        product.cj_last_sync = datetime.utcnow()
        product.synced_at = datetime.utcnow()
        
        db.session.commit()
        logger.info(f"[Admin] Produit {pid} enrichi: {', '.join(enriched_fields)}")
        
        return jsonify({
            'success': True,
            'message': f'Produit enrichi: {", ".join(enriched_fields) or "aucun changement"}',
            'enriched_fields': enriched_fields,
            'rating': product.rating_average,
            'review_count': product.rating_count
        }), 200
        
    except Exception as e:
        logger.error(f"[Admin] Erreur enrichissement: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@bp.route('/categories/visible', methods=['POST'])
@login_required
def get_visible_categories():
    """
    Récupérer les catégories CJ visibles avec hiérarchie et mapping MPS
    POST /admin/api/cj/categories/visible
    """
    try:
        from models.category import Category
        from models.product import Product
        from models.api_provider import CategoryMapping, ApiProvider
        from sqlalchemy import func
        import json
        
        # Récupérer toutes les catégories CJ (même si visible=False)
        categories = Category.query.filter(
            Category.cj_category_id.isnot(None)
        ).order_by(Category.level, Category.name).all()
        
        # Récupérer tous les mappings CJ en une seule requête
        provider = ApiProvider.query.filter_by(slug='cj-dropshipping').first()
        mappings_dict = {}
        if provider:
            mappings = CategoryMapping.query.filter_by(provider_id=provider.id).all()
            for m in mappings:
                mps_cat = Category.query.get(m.mps_category_id)
                mappings_dict[m.external_category_id] = {
                    'id': m.id,
                    'mps_category_id': m.mps_category_id,
                    'mps_category_name': mps_cat.name if mps_cat else 'Inconnue',
                    'apply_markup': m.apply_markup,
                    'auto_import': m.auto_import
                }
        
        # Calculer le vrai nombre de produits par catégorie CJ
        # en comptant les produits dont le cj_raw_data contient le cj_category_id
        cj_product_counts = {}
        products_with_raw = Product.query.filter(Product.cj_raw_data.isnot(None)).all()
        for p in products_with_raw:
            try:
                raw = json.loads(p.cj_raw_data)
                cj_cat_id = raw.get('categoryId') or raw.get('category_id') or ''
                if cj_cat_id:
                    cj_cat_id = str(cj_cat_id)
                    cj_product_counts[cj_cat_id] = cj_product_counts.get(cj_cat_id, 0) + 1
            except (json.JSONDecodeError, AttributeError):
                pass
        
        # Récupérer uniquement les catégories MPS (sans cj_category_id) pour le select
        all_mps_categories = Category.query.filter(
            Category.cj_category_id.is_(None),
            Category.slug != 'non-classe'
        ).order_by(Category.order, Category.name).all()
        mps_categories_list = [{
            'id': c.id,
            'name': c.name,
            'name_fr': c.name_fr,
            'level': c.level
        } for c in all_mps_categories]
        
        # Construire un index id -> cj_category_id pour calculer les totaux parents
        id_to_cj_id = {cat.id: cat.cj_category_id for cat in categories}
        parent_map = {cat.id: cat.parent_id for cat in categories}
        
        # Calculer les compteurs cumulés (parent = somme des enfants)
        cumulative_counts = {}
        for cat in categories:
            cumulative_counts[cat.cj_category_id] = cj_product_counts.get(cat.cj_category_id, 0)
        
        # Ajouter les compteurs des enfants aux parents (N3 -> N2 -> N1)
        for cat in sorted(categories, key=lambda c: -c.level):
            if cat.parent_id and cat.parent_id in id_to_cj_id:
                parent_cj_id = id_to_cj_id[cat.parent_id]
                if parent_cj_id:
                    cumulative_counts[parent_cj_id] = cumulative_counts.get(parent_cj_id, 0) + cumulative_counts.get(cat.cj_category_id, 0)
        
        # Formater en structure hiérarchique
        categories_data = []
        for cat in categories:
            mapping = mappings_dict.get(cat.cj_category_id)
            categories_data.append({
                'id': cat.id,
                'cj_category_id': cat.cj_category_id,
                'name': cat.name,
                'name_fr': cat.name_fr,
                'level': cat.level,
                'parent_id': cat.parent_id,
                'product_count': cumulative_counts.get(cat.cj_category_id, 0),
                'visible': cat.visible,
                'path': cat.full_path,
                'mapping': mapping
            })
        
        return jsonify({
            'success': True,
            'categories': categories_data,
            'mps_categories': mps_categories_list
        }), 200
        
    except Exception as e:
        logger.error(f"[Admin] Erreur get_visible_categories: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@bp.route('/category/update', methods=['POST'])
@login_required
def update_category():
    """
    Mettre à jour une catégorie CJ (nom FR, visibilité, mapping MPS)
    + réassigner automatiquement les produits CJ vers la catégorie MPS mappée
    POST /admin/api/cj/category/update
    Body: {category_id: int, name_fr: str, visible: bool, mps_category_id: int|null}
    """
    try:
        from models.category import Category
        from models.api_provider import CategoryMapping, ApiProvider
        from models.product import Product
        import json
        
        data = request.get_json()
        category_id = data.get('category_id')
        
        if not category_id:
            return jsonify({'success': False, 'message': 'category_id requis'}), 400
        
        cat = Category.query.get(category_id)
        if not cat:
            return jsonify({'success': False, 'message': 'Catégorie non trouvée'}), 404
        
        # Mise à jour nom FR
        if 'name_fr' in data:
            cat.name_fr = data['name_fr'].strip() if data['name_fr'] else None
        
        # Mise à jour visibilité
        if 'visible' in data:
            cat.visible = bool(data['visible'])
        
        # Mise à jour mapping MPS + réassignation des produits
        products_moved = 0
        if 'mps_category_id' in data:
            provider = ApiProvider.query.filter_by(slug='cj-dropshipping').first()
            if provider and cat.cj_category_id:
                existing_mapping = CategoryMapping.query.filter_by(
                    provider_id=provider.id,
                    external_category_id=cat.cj_category_id
                ).first()
                
                mps_cat_id = data['mps_category_id']
                
                if mps_cat_id:
                    mps_cat_id = int(mps_cat_id)
                    if existing_mapping:
                        existing_mapping.mps_category_id = mps_cat_id
                    else:
                        new_mapping = CategoryMapping(
                            provider_id=provider.id,
                            external_category_id=cat.cj_category_id,
                            external_category_name=cat.name,
                            mps_category_id=mps_cat_id,
                            auto_import=True,
                            apply_markup=1.3
                        )
                        db.session.add(new_mapping)
                    
                    # Réassigner les produits CJ vers la catégorie MPS
                    # Collecter cette catégorie CJ + tous ses enfants (N2, N3)
                    cj_cat_ids = _collect_cj_category_ids(cat)
                    products_moved = _reassign_products_to_mps(cj_cat_ids, mps_cat_id)
                    
                elif existing_mapping:
                    # Mapping supprimé : remettre les produits dans "Non classé"
                    cj_cat_ids = _collect_cj_category_ids(cat)
                    non_classe = Category.query.filter_by(slug='non-classe').first()
                    if non_classe:
                        products_moved = _reassign_products_to_mps(cj_cat_ids, non_classe.id)
                    db.session.delete(existing_mapping)
        
        db.session.commit()
        
        msg = f'Catégorie "{cat.name}" mise à jour'
        if products_moved > 0:
            msg += f' — {products_moved} produits réassignés'
        
        logger.info(f"[Admin] {msg}")
        return jsonify({
            'success': True,
            'message': msg,
            'products_moved': products_moved
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"[Admin] Erreur update_category: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


def _collect_cj_category_ids(category):
    """Collecter les cj_category_id d'une catégorie CJ et tous ses enfants"""
    from models.category import Category
    
    cj_ids = set()
    if category.cj_category_id:
        cj_ids.add(category.cj_category_id)
    
    # Récupérer les enfants directs (N2)
    children = Category.query.filter_by(parent_id=category.id).filter(
        Category.cj_category_id.isnot(None)
    ).all()
    
    for child in children:
        if child.cj_category_id:
            cj_ids.add(child.cj_category_id)
        # Récupérer les petits-enfants (N3)
        grandchildren = Category.query.filter_by(parent_id=child.id).filter(
            Category.cj_category_id.isnot(None)
        ).all()
        for gc in grandchildren:
            if gc.cj_category_id:
                cj_ids.add(gc.cj_category_id)
    
    return cj_ids


def _reassign_products_to_mps(cj_cat_ids, mps_category_id):
    """Réassigner les produits dont le cj_raw_data contient un category_id dans cj_cat_ids"""
    from models.product import Product
    import json
    
    if not cj_cat_ids:
        return 0
    
    # Récupérer tous les produits qui ont un cj_raw_data
    products = Product.query.filter(Product.cj_raw_data.isnot(None)).all()
    
    count = 0
    for product in products:
        try:
            raw = json.loads(product.cj_raw_data)
            # Supporter les 2 formats : camelCase (categoryId) et snake_case (category_id)
            product_cj_cat_id = raw.get('categoryId') or raw.get('category_id') or ''
            if product_cj_cat_id in cj_cat_ids:
                if product.category_id != mps_category_id:
                    product.category_id = mps_category_id
                    count += 1
        except (json.JSONDecodeError, AttributeError):
            continue
    
    return count


@bp.route('/products/by-category', methods=['POST'])
@login_required
def get_products_by_category():
    """
    Récupérer les produits d'une catégorie CJ avec pagination
    POST /admin/api/cj/products/by-category
    Body: {category_id: int, page: int, per_page: int, include_hidden: bool, search: str}
    
    Cherche les produits par leur catégorie CJ originale (stockée dans cj_raw_data)
    """
    try:
        from models.product import Product
        from models.category import Category
        from sqlalchemy import or_
        
        data = request.form or request.get_json() or {}
        category_id = data.get('category_id') or data.get('category_cj_id')
        page = int(data.get('page', 1))
        per_page = int(data.get('per_page', 20))
        include_hidden = data.get('include_hidden', '0') == '1'
        search_term = data.get('search', '').strip()
        
        if not category_id:
            return jsonify({
                'success': False,
                'message': 'category_id requis'
            }), 400
        
        # Trouver la catégorie CJ par ID BDD
        category = db.session.get(Category, int(category_id))
        if not category:
            return jsonify({
                'success': False,
                'message': 'Catégorie non trouvée'
            }), 404
        
        # Récupérer les cj_category_id de toutes les catégories CJ concernées
        cj_cat_ids = []
        if category.cj_category_id:
            cj_cat_ids.append(category.cj_category_id)
        
        # Si niveau 1 ou 2, inclure toutes les sous-catégories CJ
        if category.level == 1:
            level2_cats = Category.query.filter_by(parent_id=category.id).all()
            for cat2 in level2_cats:
                if cat2.cj_category_id:
                    cj_cat_ids.append(cat2.cj_category_id)
                level3_cats = Category.query.filter_by(parent_id=cat2.id).all()
                for cat3 in level3_cats:
                    if cat3.cj_category_id:
                        cj_cat_ids.append(cat3.cj_category_id)
        elif category.level == 2:
            level3_cats = Category.query.filter_by(parent_id=category.id).all()
            for cat3 in level3_cats:
                if cat3.cj_category_id:
                    cj_cat_ids.append(cat3.cj_category_id)
        
        # Chercher les produits dont le cj_raw_data contient un de ces category_id CJ
        # On utilise LIKE sur le JSON brut pour filtrer efficacement
        query = Product.query.filter(
            Product.cj_pid.isnot(None)
        )
        
        if cj_cat_ids:
            # Construire un filtre OR sur cj_raw_data pour chaque cj_category_id
            cj_filters = [Product.cj_raw_data.like(f'%"categoryId": "{cid}"%') for cid in cj_cat_ids]
            query = query.filter(or_(*cj_filters))
        
        # Recherche par PID, SKU ou nom
        if search_term:
            query = query.filter(
                or_(
                    Product.cj_pid.ilike(f'%{search_term}%'),
                    Product.sku.ilike(f'%{search_term}%'),
                    Product.name.ilike(f'%{search_term}%')
                )
            )
        
        # Dans l'admin CJ, on affiche tous les produits par défaut (actifs et inactifs)
        # L'utilisateur peut filtrer avec include_hidden si nécessaire
        if include_hidden == False:  # Si explicitement False, filtrer les inactifs
            query = query.filter_by(is_active=True)
        
        # Pagination
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Formater les produits
        products_data = []
        for product in pagination.items:
            # Calculer le markup réel appliqué
            markup_percentage = 0
            if product.cost_price and product.price and product.cost_price > 0:
                markup_percentage = pricing_service.calculate_markup_percentage(product.price, product.cost_price)
            
            products_data.append({
                'id': product.id,
                'cj_pid': product.cj_pid,
                'name': product.name,
                'sku': product.sku,
                'price': product.price,
                'cost_price': product.cost_price,
                'compare_price': product.compare_price,
                'suggested_price': product.suggested_price,
                'stock': product.stock,
                'image_url': product.image_url,
                'published': product.published,
                'is_active': product.is_active,
                'markup_percentage': markup_percentage,
                'synced_at': product.synced_at.isoformat() if product.synced_at else None
            })
        
        return jsonify({
            'success': True,
            'products': products_data,
            'pagination': {
                'current_page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_prev': pagination.has_prev,
                'has_next': pagination.has_next,
                'from': (pagination.page - 1) * pagination.per_page + 1 if pagination.items else 0,
                'to': (pagination.page - 1) * pagination.per_page + len(pagination.items)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"[Admin] Erreur get_products_by_category: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@bp.route('/products/search', methods=['POST'])
@login_required
def search_products():
    """
    Recherche globale de produits CJ par PID, SKU ou nom
    POST /admin/api/cj/products/search
    Body: {search: str, page: int, per_page: int}
    """
    try:
        from sqlalchemy import or_
        
        data = request.form or request.get_json() or {}
        search_term = data.get('search', '').strip()
        page = int(data.get('page', 1))
        per_page = int(data.get('per_page', 20))
        
        if not search_term:
            return jsonify({
                'success': False,
                'message': 'Terme de recherche requis'
            }), 400
        
        # Recherche dans tous les produits CJ
        query = Product.query.filter(
            Product.cj_pid.isnot(None),
            or_(
                Product.cj_pid.ilike(f'%{search_term}%'),
                Product.sku.ilike(f'%{search_term}%'),
                Product.name.ilike(f'%{search_term}%')
            )
        )
        
        # Pagination
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Formater les produits
        products_data = []
        for product in pagination.items:
            # Calculer le markup réel appliqué
            markup_percentage = 0
            if product.cost_price and product.price and product.cost_price > 0:
                markup_percentage = pricing_service.calculate_markup_percentage(product.price, product.cost_price)
            
            products_data.append({
                'id': product.id,
                'cj_pid': product.cj_pid,
                'name': product.name,
                'sku': product.sku,
                'price': product.price,
                'cost_price': product.cost_price,
                'compare_price': product.compare_price,
                'suggested_price': product.suggested_price,
                'stock': product.stock,
                'image_url': product.image_url,
                'published': product.published,
                'is_active': product.is_active,
                'markup_percentage': markup_percentage,
                'synced_at': product.synced_at.isoformat() if product.synced_at else None,
                'category_id': product.category_id
            })
        
        return jsonify({
            'success': True,
            'products': products_data,
            'pagination': {
                'current_page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_prev': pagination.has_prev,
                'has_next': pagination.has_next,
                'from': (pagination.page - 1) * pagination.per_page + 1 if pagination.items else 0,
                'to': (pagination.page - 1) * pagination.per_page + len(pagination.items)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"[Admin] Erreur search_products: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@bp.route('/product/<int:product_id>/details', methods=['GET'])
@login_required
def get_product_details_from_db(product_id):
    """
    Récupérer les détails complets d'un produit depuis la BDD (sans appel API CJ)
    GET /admin/api/cj/product/<id>/details
    """
    try:
        from models.product_variant import ProductVariant
        
        product = Product.query.get(product_id)
        
        if not product:
            return jsonify({'success': False, 'message': 'Produit introuvable'}), 404
        
        # Récupérer les variantes
        variants = ProductVariant.query.filter_by(product_id=product_id, active=True).all()
        variants_data = [{
            'id': v.id,
            'cj_vid': v.cj_vid,
            'variant_key': v.variant_key,
            'color': v.color,
            'size': v.size,
            'price': v.price,
            'stock': v.stock,
            'image_url': v.image_url,
            'weight': v.weight,
            'sku': v.sku,
            'active': v.active,
            'display_name': v.display_name
        } for v in variants]
        
        # Images supplémentaires
        images = product.get_images_list() if hasattr(product, 'get_images_list') else []
        
        # Corriger image_url si c'est un JSON array
        import json as json_lib
        image_url = product.image_url or ''
        if image_url.strip().startswith('['):
            try:
                parsed = json_lib.loads(image_url)
                if isinstance(parsed, list) and parsed:
                    image_url = parsed[0]
                    # Ajouter les autres images à la liste
                    for img in parsed[1:]:
                        if img not in images:
                            images.append(img)
            except (json_lib.JSONDecodeError, ValueError):
                pass
        
        # Corriger les images qui sont des JSON arrays non parsés
        clean_images = []
        for img in images:
            if isinstance(img, str) and img.strip().startswith('['):
                try:
                    parsed = json_lib.loads(img)
                    if isinstance(parsed, list):
                        clean_images.extend(parsed)
                    else:
                        clean_images.append(img)
                except (json_lib.JSONDecodeError, ValueError):
                    clean_images.append(img)
            else:
                clean_images.append(img)
        images = clean_images
        
        # S'assurer que image_url est dans la liste d'images
        if image_url and image_url not in images:
            images.insert(0, image_url)
        
        return jsonify({
            'success': True,
            'product': {
                'id': product.id,
                'cj_pid': product.cj_pid,
                'name': product.name,
                'sku': product.sku,
                'description': product.description,
                'price': product.price,
                'cost_price': product.cost_price,
                'compare_price': product.compare_price,
                'suggested_price': product.suggested_price,
                'stock': product.stock,
                'image_url': image_url,
                'images': images,
                'weight': product.weight,
                'length': product.length,
                'width': product.width,
                'height': product.height,
                'material': product.material,
                'published': product.published,
                'is_active': product.is_active,
                'rating_average': product.rating_average,
                'rating_count': product.rating_count,
                'synced_at': product.synced_at.isoformat() if product.synced_at else None,
                'cj_last_sync': product.cj_last_sync.isoformat() if product.cj_last_sync else None,
                'created_at': product.created_at.isoformat() if product.created_at else None,
                'variants': variants_data,
                'variants_count': len(variants_data),
                'total_variant_stock': sum(v.stock or 0 for v in variants)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Erreur get_product_details_from_db: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/product/<int:product_id>/cj-raw-data', methods=['GET'])
@login_required
def get_product_cj_raw_data(product_id):
    """
    Récupérer les données JSON brutes de CJ pour un produit
    """
    try:
        product = Product.query.get(product_id)
        
        if not product or not product.cj_pid:
            return jsonify({
                'success': False,
                'message': 'Produit CJ introuvable'
            }), 404
        
        # Utiliser la fonction get_cj_api() qui gère la configuration
        cj_api = get_cj_api()
        
        # Récupérer les données brutes depuis l'API CJ
        raw_data = cj_api.get_product_details(product.cj_pid)
        
        if not raw_data:
            return jsonify({
                'success': False,
                'message': 'Impossible de récupérer les données CJ',
                'raw_data': None
            })
        
        return jsonify({
            'success': True,
            'cj_pid': product.cj_pid,
            'raw_data': raw_data
        })
    
    except Exception as e:
        logger.error(f"Erreur get_product_cj_raw_data: {e}")
        return jsonify({
            'success': False,
            'message': str(e),
            'raw_data': None
        }), 500


@bp.route('/product/<int:product_id>/sync-variants', methods=['POST'])
@login_required
def sync_product_variants(product_id):
    """
    Synchroniser les variantes d'un produit depuis CJ API
    """
    try:
        from services.cj_variant_sync_service import CjVariantSyncService
        from extensions import db, cache
        
        cj_api = get_cj_api()
        sync_service = CjVariantSyncService(cj_api)
        
        result = sync_service.sync_product_variants(product_id)
        
        # Mettre à jour le stock principal depuis les variantes
        if result['success']:
            product = Product.query.get(product_id)
            if product:
                updated = product.update_stock_from_variants()
                if updated:
                    db.session.commit()
                    result['stock_updated'] = True
                    result['total_stock'] = product.stock
                    logger.info(f"[Admin] Stock principal mis à jour: {product.stock}")
                
                # Invalider le cache de la page produit pour afficher les nouvelles variantes
                cache.delete_memoized('product_detail', product_id)
                cache.delete(f'product_detail_{product_id}')
                logger.info(f"[Admin] Cache de la page produit {product_id} invalidé")
                
                # Récupérer les variantes synchronisées pour les retourner
                from models.product_variant import ProductVariant
                variants = ProductVariant.query.filter_by(product_id=product_id, active=True).all()
                result['variants'] = [{
                    'id': v.id,
                    'cj_vid': v.cj_vid,
                    'variant_key': v.variant_key,
                    'color': v.color,
                    'size': v.size,
                    'price': v.price,
                    'stock': v.stock,
                    'image_url': v.image_url,
                    'weight': v.weight,
                    'sku': v.sku,
                    'active': v.active,
                    'display_name': v.display_name
                } for v in variants]
        
        return jsonify(result), 200 if result['success'] else 500
        
    except Exception as e:
        logger.error(f"Erreur sync variantes: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@bp.route('/variant/<int:variant_id>/sync-stock', methods=['POST'])
def sync_variant_stock(variant_id):
    """
    Synchroniser le stock d'une variante depuis CJ API
    """
    try:
        from services.cj_variant_sync_service import CjVariantSyncService
        from models.product_variant import ProductVariant
        from extensions import db
        
        cj_api = get_cj_api()
        sync_service = CjVariantSyncService(cj_api)
        
        result = sync_service.sync_variant_stock(variant_id)
        
        # Mettre à jour le stock principal du produit
        if result['success']:
            variant = ProductVariant.query.get(variant_id)
            if variant and variant.product_id:
                product = Product.query.get(variant.product_id)
                if product:
                    updated = product.update_stock_from_variants()
                    if updated:
                        db.session.commit()
                        result['product_stock_updated'] = True
                        result['product_total_stock'] = product.stock
        
        return jsonify(result), 200 if result['success'] else 500
        
    except Exception as e:
        logger.error(f"Erreur sync stock variante: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@bp.route('/sync-all-stocks', methods=['POST'])
def sync_all_stocks():
    """
    Synchroniser les stocks de tous les produits CJ en masse via listV2
    listV2 est le seul endpoint CJ qui retourne warehouseInventoryNum
    """
    try:
        from extensions import db
        import time
        
        logger.info("[SyncMasse] Démarrage synchronisation masse via listV2")
        start_time = time.time()
        
        cj_api = get_cj_api()
        
        # Indexer tous les produits CJ par PID
        all_products = Product.query.filter(Product.cj_pid.isnot(None)).all()
        pid_to_product = {str(p.cj_pid): p for p in all_products}
        
        products_processed = 0
        products_updated = 0
        products_failed = 0
        variants_updated = 0
        variants_failed = 0
        
        # Paginer sur listV2 (max 10 pages pour éviter timeout)
        max_pages = 10
        for page in range(1, max_pages + 1):
            try:
                result_v2 = cj_api.get_products_v2(page=page, page_size=100)
                
                if not result_v2.get('products'):
                    break
                
                for p in result_v2['products']:
                    pid = str(p.get('pid', ''))
                    stock = p.get('stock', 0)
                    products_processed += 1
                    
                    if pid in pid_to_product:
                        product = pid_to_product[pid]
                        old_stock = product.stock
                        
                        if stock > 0:
                            if old_stock != stock:
                                product.stock = stock
                                products_updated += 1
                            product.stock_checked = True
                        else:
                            # Ne pas écraser stock par défaut (999) sauf si déjà vérifié
                            if product.stock_checked and old_stock != 0:
                                product.stock = 0
                                products_updated += 1
                
                db.session.commit()
                
                if page >= result_v2.get('total_pages', 0):
                    break
                
                time.sleep(1.5)
                
            except Exception as e:
                logger.error(f"[SyncMasse] Erreur page {page}: {e}")
                products_failed += 1
                time.sleep(5)
        
        db.session.commit()
        duration = f"{int(time.time() - start_time)}s"
        
        return jsonify({
            'success': True,
            'message': f'Synchronisation terminée: {products_updated}/{products_processed} produits mis à jour',
            'products_processed': products_processed,
            'products_updated': products_updated,
            'products_failed': products_failed,
            'variants_updated': variants_updated,
            'variants_failed': variants_failed,
            'duration': duration
        }), 200
        
    except Exception as e:
        logger.error(f"[SyncMasse] Erreur critique: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Erreur: {str(e)}'
        }), 500


@bp.route('/sync-stats', methods=['GET'])
def get_sync_stats():
    """
    Obtenir les statistiques de synchronisation
    """
    try:
        from services.background_sync_service import BackgroundSyncService
        
        cj_api = get_cj_api()
        sync_service = BackgroundSyncService(db, cj_api)
        
        stats = sync_service.get_sync_stats()
        
        return jsonify({
            'success': True,
            'stats': stats
        }), 200
        
    except Exception as e:
        logger.error(f"Erreur get_sync_stats: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@bp.route('/sync-batch', methods=['POST'])
def sync_batch():
    """
    Synchroniser un batch de produits en arrière-plan
    """
    try:
        from services.background_sync_service import BackgroundSyncService
        
        data = request.get_json() or {}
        batch_size = data.get('batch_size', 10)
        
        cj_api = get_cj_api()
        sync_service = BackgroundSyncService(db, cj_api)
        
        result = sync_service.sync_batch(batch_size)
        
        return jsonify(result), 200 if result['success'] else 500
        
    except Exception as e:
        logger.error(f"Erreur sync_batch: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@bp.route('/product/<int:product_id>/sync-all-variants-stock', methods=['POST'])
@login_required
def sync_all_variants_stock(product_id):
    """
    Synchroniser le stock de toutes les variantes d'un produit
    """
    try:
        from services.cj_variant_sync_service import CjVariantSyncService
        
        cj_api = get_cj_api()
        sync_service = CjVariantSyncService(cj_api)
        
        result = sync_service.sync_all_variants_stock(product_id)
        
        return jsonify(result), 200 if result['success'] else 500
        
    except Exception as e:
        logger.error(f"Erreur sync stock toutes variantes: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@bp.route('/variant/<int:variant_id>/stock-status', methods=['GET'])
def get_variant_stock_status(variant_id):
    """
    Obtenir le statut du stock d'une variante en temps réel
    """
    try:
        from services.cj_variant_sync_service import CjVariantSyncService
        
        cj_api = get_cj_api()
        sync_service = CjVariantSyncService(cj_api)
        
        result = sync_service.get_variant_stock_status(variant_id)
        
        return jsonify(result), 200 if result['success'] else 500
        
    except Exception as e:
        logger.error(f"Erreur get stock status: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@bp.route('/product/<int:product_id>/sync-stock', methods=['POST'])
@login_required
def sync_product_stock(product_id):
    """
    Synchroniser le stock du produit principal depuis CJ API
    Utilise listV2 (seul endpoint avec warehouseInventoryNum) ou variantes
    """
    try:
        from extensions import db
        from services.cj_variant_sync_service import CjVariantSyncService
        
        product = Product.query.get(product_id)
        
        if not product or not product.cj_pid:
            return jsonify({
                'success': False,
                'message': 'Produit CJ introuvable'
            }), 404
        
        cj_api = get_cj_api()
        old_stock = product.stock
        new_stock = 0
        method_used = ''
        
        # Méthode 1: listV2 d'abord (seul endpoint fiable pour le stock)
        try:
            result_v2 = cj_api.get_products_v2(page=1, page_size=5, keyword=product.sku or product.cj_pid)
            if result_v2.get('products'):
                for p in result_v2['products']:
                    if str(p.get('pid')) == str(product.cj_pid):
                        new_stock = p.get('stock', 0)
                        method_used = 'listV2'
                        break
        except Exception as e:
            logger.warning(f"listV2 échouée: {e}")
        
        # Méthode 2: Si listV2 n'a rien trouvé, essayer variantes
        if new_stock == 0:
            try:
                sync_service = CjVariantSyncService(cj_api)
                result = sync_service.sync_product_variants(product.id)
                if result.get('success'):
                    variant_stock = product.calculate_total_stock_from_variants()
                    if variant_stock > 0:
                        new_stock = variant_stock
                        method_used = 'variantes'
            except Exception as e:
                logger.warning(f"Sync variantes échouée: {e}")
        
        # Logique stock_checked : ne pas écraser stock par défaut (999) si API retourne 0
        if new_stock > 0:
            product.stock = new_stock
            product.stock_checked = True
        elif product.stock_checked:
            # Stock déjà vérifié avant → on peut mettre à 0
            product.stock = 0
        else:
            # Jamais vérifié, garder le stock par défaut
            new_stock = old_stock
            method_used = method_used or 'conservé (défaut dropshipping)'
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Stock mis à jour: {old_stock} → {new_stock} (via {method_used or "API"})',
            'old_stock': old_stock,
            'new_stock': new_stock,
            'method': method_used
        }), 200
        
    except Exception as e:
        logger.error(f"Erreur sync_product_stock: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@bp.route('/product/<int:product_id>/save-cj-data', methods=['POST'])
@login_required
def save_product_cj_data(product_id):
    """
    Sauvegarder les données CJ chargées dans le modal
    POST /admin/api/cj/product/<id>/save-cj-data
    Body: {description, images, weight, etc.}
    """
    try:
        from extensions import db
        
        product = Product.query.get(product_id)
        
        if not product or not product.cj_pid:
            return jsonify({
                'success': False,
                'message': 'Produit CJ introuvable'
            }), 404
        
        data = request.get_json() or {}
        
        # Mettre à jour les champs si fournis
        if 'description' in data and data['description']:
            product.description = data['description']
        
        if 'image_url' in data and data['image_url']:
            product.image_url = data['image_url']
        
        if 'weight' in data and data['weight']:
            product.weight = float(data['weight'])
        
        if 'name' in data and data['name']:
            product.name = data['name']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Données sauvegardées'
        }), 200
        
    except Exception as e:
        logger.error(f"Erreur save_product_cj_data: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@bp.route('/shipping/sync', methods=['POST'])
@login_required
def sync_shipping_rates():
    """Lancer la pré-sync des frais de livraison CJ"""
    try:
        from models.shipping_rate import ShippingRate
        from models.product_variant import ProductVariant
        import time
        
        data = request.get_json() or {}
        countries = data.get('countries', ['FR'])
        limit = data.get('limit', 50)
        refresh_only = data.get('refresh_only', True)
        max_age_days = data.get('max_age_days', 7)
        
        cj_api = get_cj_api()
        
        query = Product.query.filter(
            Product.cj_pid.isnot(None),
            Product.is_active == True
        ).order_by(Product.id)
        
        if limit:
            query = query.limit(limit)
        
        products = query.all()
        
        stats = {'synced': 0, 'empty': 0, 'skipped': 0, 'errors': 0}
        
        for product in products:
            for country in countries:
                if refresh_only:
                    existing = ShippingRate.get_for_product(product.id, country)
                    if existing and not existing.is_expired(max_age_days):
                        stats['skipped'] += 1
                        continue
                
                # Récupérer le SKU CJ de la première variante active
                variant = ProductVariant.query.filter_by(
                    product_id=product.id, active=True
                ).filter(ProductVariant.sku.isnot(None), ProductVariant.sku != '').first()
                sku = variant.sku if variant else None
                
                if not sku:
                    stats['errors'] += 1
                    continue
                
                try:
                    response = cj_api._make_request('POST', 'logistic/freightCalculateTip', json={
                        'reqDTOS': [{
                            'srcAreaCode': 'CN',
                            'destAreaCode': country,
                            'productProp': ['COMMON'],
                            'freightTrialSkuList': [{'skuQuantity': 1, 'sku': sku}],
                            'skuList': [sku],
                            'platforms': ['Shopify']
                        }]
                    })
                    
                    if response is None:
                        stats['errors'] += 1
                        continue
                    
                    if response.get('result') is True and response.get('data'):
                        methods = []
                        USD_TO_EUR = 0.92
                        for m in response['data']:
                            option = m.get('option', {})
                            price_usd = float(m.get('discountFee', m.get('postage', 0)))
                            price_eur = round(price_usd * USD_TO_EUR, 2)
                            methods.append({
                                'code': option.get('enName', 'UNKNOWN'),
                                'name': option.get('enName', 'Méthode inconnue'),
                                'price': price_eur,
                                'price_usd': price_usd,
                                'price_cny': float(m.get('discountFeeCNY', m.get('postageCNY', 0))),
                                'delivery_time': m.get('arrivalTime', 'N/A'),
                                'source': 'cj'
                            })
                        ShippingRate.upsert(product.id, country, methods, source='cj')
                        stats['synced'] += 1
                    else:
                        ShippingRate.upsert(product.id, country, [], source='cj_empty')
                        stats['empty'] += 1
                    
                    time.sleep(1.6)
                    
                except Exception as e:
                    logger.error(f"Erreur sync shipping P{product.id}: {e}")
                    stats['errors'] += 1
            
            if stats['synced'] % 20 == 0 and stats['synced'] > 0:
                db.session.commit()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'stats': stats,
            'message': f"Sync terminée: {stats['synced']} OK, {stats['empty']} vides, {stats['skipped']} ignorés, {stats['errors']} erreurs"
        })
        
    except Exception as e:
        logger.error(f"Erreur sync_shipping_rates: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/shipping/stats', methods=['GET'])
@login_required
def shipping_stats():
    """Statistiques du cache de frais de livraison"""
    try:
        from models.shipping_rate import ShippingRate
        from sqlalchemy import func
        
        total = ShippingRate.query.count()
        with_methods = ShippingRate.query.filter(ShippingRate.source == 'cj').count()
        empty = ShippingRate.query.filter(ShippingRate.source == 'cj_empty').count()
        
        total_products = Product.query.filter(
            Product.cj_pid.isnot(None), Product.is_active == True
        ).count()
        
        # Stats par pays
        by_country = db.session.query(
            ShippingRate.country_code,
            func.count(ShippingRate.id),
            func.sum(db.case((ShippingRate.source == 'cj', 1), else_=0))
        ).group_by(ShippingRate.country_code).all()
        
        countries_stats = [{
            'country': row[0],
            'total': row[1],
            'with_methods': int(row[2] or 0)
        } for row in by_country]
        
        return jsonify({
            'success': True,
            'total_rates': total,
            'with_methods': with_methods,
            'empty': empty,
            'total_cj_products': total_products,
            'coverage_pct': round(total / total_products * 100, 1) if total_products > 0 else 0,
            'by_country': countries_stats
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
