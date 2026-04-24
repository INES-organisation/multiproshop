"""
Routes pour la gestion des intégrations API dans l'admin
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from functools import wraps
from extensions import db
from models.api_provider import ApiProvider, CategoryMapping, ProductSource, ApiSyncLog
from models.category import Category
from models.product import Product
from services.api_providers import CJDropshippingProvider, PrintifyProvider, AmazonProvider, EbayProvider
from datetime import datetime

api_mgmt_bp = Blueprint('api_management', __name__, url_prefix='/admin/api')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Vous devez être connecté', 'error')
            return redirect(url_for('auth.login'))
        if not current_user.role or current_user.role.name != 'admin':
            flash('Accès non autorisé', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

# ============================================================================
# GESTION DES PROVIDERS
# ============================================================================

@api_mgmt_bp.route('/providers')
@login_required
@admin_required
def list_providers():
    """Liste des providers d'API"""
    from models.product import Product
    
    providers = ApiProvider.query.all()
    
    # Compter les produits réels (Product) au lieu des ProductSource
    total_products_real = db.session.query(Product).join(
        ProductSource, Product.id == ProductSource.product_id
    ).distinct().count()
    
    # Calculer le nombre de produits réels pour chaque provider
    for provider in providers:
        provider.real_products_count = db.session.query(Product).join(
            ProductSource, Product.id == ProductSource.product_id
        ).filter(
            ProductSource.provider_id == provider.id
        ).distinct().count()
    
    # Statistiques
    stats = {
        'total': len(providers),
        'active': sum(1 for p in providers if p.is_active),
        'connected': sum(1 for p in providers if p.is_connected),
        'total_products': total_products_real,
        'total_revenue': sum(p.total_revenue for p in providers)
    }
    
    return render_template('admin/api/providers.html', providers=providers, stats=stats)

@api_mgmt_bp.route('/providers/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_provider():
    """Créer un nouveau provider"""
    if request.method == 'POST':
        try:
            provider = ApiProvider(
                name=request.form['name'],
                slug=request.form['slug'],
                description=request.form.get('description'),
                provider_type=request.form['provider_type'],
                api_endpoint=request.form.get('api_endpoint'),
                api_version=request.form.get('api_version'),
                auth_type=request.form.get('auth_type'),
                api_key=request.form.get('api_key'),
                api_secret=request.form.get('api_secret'),
                rate_limit=int(request.form.get('rate_limit') or 0) or None,
                daily_quota=int(request.form.get('daily_quota') or 0) or None,
                is_active=request.form.get('is_active') == 'on'
            )
            
            db.session.add(provider)
            db.session.commit()
            
            flash(f'Provider {provider.name} créé avec succès', 'success')
            return redirect(url_for('api_management.list_providers'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'error')
    
    # Templates de providers prédéfinis
    templates = {
        'cj-dropshipping': {
            'name': 'CJ Dropshipping',
            'slug': 'cj-dropshipping',
            'provider_type': 'dropshipping',
            'api_endpoint': 'https://developers.cjdropshipping.com/api2.0/v1',
            'api_version': 'v1',
            'auth_type': 'signature'
        },
        'printify': {
            'name': 'Printify',
            'slug': 'printify',
            'provider_type': 'print-on-demand',
            'api_endpoint': 'https://api.printify.com/v1',
            'api_version': 'v1',
            'auth_type': 'bearer'
        },
        'amazon': {
            'name': 'Amazon Product Advertising',
            'slug': 'amazon',
            'provider_type': 'affiliate',
            'api_endpoint': 'https://webservices.amazon.fr/paapi5',
            'api_version': 'v5',
            'auth_type': 'signature'
        },
        'ebay': {
            'name': 'eBay Partner Network',
            'slug': 'ebay',
            'provider_type': 'affiliate',
            'api_endpoint': 'https://api.ebay.com',
            'api_version': 'v1',
            'auth_type': 'oauth'
        }
    }
    
    return render_template('admin/api/provider_form.html', provider=None, templates=templates)

@api_mgmt_bp.route('/providers/<int:provider_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_provider(provider_id):
    """Éditer un provider"""
    provider = ApiProvider.query.get_or_404(provider_id)
    
    if request.method == 'POST':
        try:
            provider.name = request.form['name']
            provider.slug = request.form['slug']
            provider.description = request.form.get('description')
            provider.provider_type = request.form['provider_type']
            provider.api_endpoint = request.form.get('api_endpoint')
            provider.api_version = request.form.get('api_version')
            provider.auth_type = request.form.get('auth_type')
            provider.api_key = request.form.get('api_key')
            provider.api_secret = request.form.get('api_secret')
            provider.rate_limit = int(request.form.get('rate_limit') or 0) or None
            provider.daily_quota = int(request.form.get('daily_quota') or 0) or None
            provider.is_active = request.form.get('is_active') == 'on'
            
            db.session.commit()
            
            flash(f'Provider {provider.name} mis à jour', 'success')
            return redirect(url_for('api_management.list_providers'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'error')
    
    return render_template('admin/api/provider_form.html', provider=provider, templates={})

@api_mgmt_bp.route('/providers/<int:provider_id>/test', methods=['POST'])
@login_required
@admin_required
def test_provider(provider_id):
    """Tester la connexion à un provider"""
    provider = ApiProvider.query.get_or_404(provider_id)
    
    try:
        # Instancier le bon service
        service = get_provider_service(provider)
        
        if service.test_connection():
            provider.is_connected = True
            db.session.commit()
            return jsonify({'success': True, 'message': 'Connexion réussie !'})
        else:
            provider.is_connected = False
            db.session.commit()
            return jsonify({'success': False, 'message': 'Échec de la connexion'}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@api_mgmt_bp.route('/providers/<int:provider_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_provider(provider_id):
    """Supprimer un provider"""
    provider = ApiProvider.query.get_or_404(provider_id)
    name = provider.name
    
    try:
        db.session.delete(provider)
        db.session.commit()
        flash(f'Provider {name} supprimé', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur: {str(e)}', 'error')
    
    return redirect(url_for('api_management.list_providers'))

# ============================================================================
# MAPPING DES CATÉGORIES
# ============================================================================

@api_mgmt_bp.route('/providers/<int:provider_id>/categories')
@login_required
@admin_required
def manage_categories(provider_id):
    """Gérer le mapping des catégories"""
    provider = ApiProvider.query.get_or_404(provider_id)
    
    # Récupérer les catégories du provider
    service = get_provider_service(provider)
    external_categories = service.get_categories()
    
    # Récupérer les catégories MPS
    mps_categories = Category.query.all()
    
    # Récupérer les mappings existants
    mappings = CategoryMapping.query.filter_by(provider_id=provider_id).all()
    
    return render_template('admin/api/category_mapping.html',
                         provider=provider,
                         external_categories=external_categories,
                         mps_categories=mps_categories,
                         mappings=mappings)

@api_mgmt_bp.route('/providers/<int:provider_id>/categories/map', methods=['POST'])
@login_required
@admin_required
def map_category(provider_id):
    """Créer un mapping de catégorie"""
    try:
        mapping = CategoryMapping(
            provider_id=provider_id,
            external_category_id=request.form['external_category_id'],
            external_category_name=request.form['external_category_name'],
            external_category_path=request.form.get('external_category_path'),
            mps_category_id=int(request.form['mps_category_id']),
            auto_import=request.form.get('auto_import') == 'on',
            apply_markup=float(request.form.get('apply_markup', 1.3))
        )
        
        db.session.add(mapping)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Mapping créé'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

@api_mgmt_bp.route('/mappings/<int:mapping_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_mapping(mapping_id):
    """Supprimer un mapping"""
    mapping = CategoryMapping.query.get_or_404(mapping_id)
    provider_id = mapping.provider_id
    
    db.session.delete(mapping)
    db.session.commit()
    
    return redirect(url_for('api_management.manage_categories', provider_id=provider_id))

# ============================================================================
# SYNCHRONISATION DES PRODUITS
# ============================================================================

@api_mgmt_bp.route('/providers/<int:provider_id>/sync', methods=['POST'])
@login_required
@admin_required
def sync_products(provider_id):
    """Synchroniser les produits d'un provider - Version synchrone"""
    provider = ApiProvider.query.get_or_404(provider_id)
    
    try:
        service = get_provider_service(provider)
        
        priority_categories = ['Echarpes & Foulards', 'Chapeaux & Casquettes', 'Gants & Moufles', 
                              'Chapeaux & Casquettes Femme', 'Gants & Moufles Femme']
        
        all_mappings = CategoryMapping.query.filter_by(provider_id=provider_id, auto_import=True).all()
        priority_mappings = [m for m in all_mappings if m.external_category_name in priority_categories]
        other_mappings = [m for m in all_mappings if m.external_category_name not in priority_categories]
        mappings = (priority_mappings + other_mappings)[:10]
        
        total_created = 0
        total_updated = 0
        total_failed = 0
        
        import random
        
        for idx, mapping in enumerate(mappings, 1):
            # Utiliser une page aléatoire entre 1 et 5 pour varier les produits
            random_page = random.randint(1, 5)
            result = service.get_products(category_id=mapping.external_category_id, page=random_page, limit=20)
            
            import time
            time.sleep(1)
            
            for product_data in result.get('products', []):
                try:
                    source = ProductSource.query.filter_by(
                        provider_id=provider_id,
                        external_product_id=product_data['external_id']
                    ).first()
                    
                    if source:
                        update_product_from_source(source, product_data, mapping)
                        total_updated += 1
                    else:
                        create_product_from_source(provider, product_data, mapping)
                        total_created += 1
                    
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    total_failed += 1
        
        return jsonify({
            'success': True,
            'created': total_created,
            'updated': total_updated,
            'failed': total_failed
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

def _sync_products_background(provider_id, sync_log_id):
    """Synchronisation en arrière-plan"""
    with app.app_context():
        try:
            provider = ApiProvider.query.get(provider_id)
            sync_log = ApiSyncLog.query.get(sync_log_id)
            service = get_provider_service(provider)
            
            priority_categories = ['Echarpes & Foulards', 'Chapeaux & Casquettes', 'Gants & Moufles', 
                                  'Chapeaux & Casquettes Femme', 'Gants & Moufles Femme']
            
            all_mappings = CategoryMapping.query.filter_by(provider_id=provider_id, auto_import=True).all()
            priority_mappings = [m for m in all_mappings if m.external_category_name in priority_categories]
            other_mappings = [m for m in all_mappings if m.external_category_name not in priority_categories]
            mappings = (priority_mappings + other_mappings)[:3]
            
            total_created = 0
            total_updated = 0
            total_failed = 0
            
            for idx, mapping in enumerate(mappings, 1):
                print(f"Synchronisation catégorie {idx}/{len(mappings)}: {mapping.external_category_name}")
                result = service.get_products(category_id=mapping.external_category_id, limit=5)
                
                import time
                time.sleep(1)
                
                for product_data in result.get('products', []):
                    try:
                        source = ProductSource.query.filter_by(
                            provider_id=provider_id,
                            external_product_id=product_data['external_id']
                        ).first()
                        
                        if source:
                            update_product_from_source(source, product_data, mapping)
                            total_updated += 1
                        else:
                            create_product_from_source(provider, product_data, mapping)
                            total_created += 1
                        
                        db.session.commit()
                    except Exception as e:
                        print(f"Erreur import produit {product_data.get('name', 'N/A')}: {e}")
                        import traceback
                        traceback.print_exc()
                        db.session.rollback()
                        total_failed += 1
            
            sync_log.status = 'success'
            sync_log.items_created = total_created
            sync_log.items_updated = total_updated
            sync_log.items_failed = total_failed
            sync_log.items_processed = total_created + total_updated + total_failed
            sync_log.completed_at = datetime.utcnow()
            sync_log.duration_seconds = int((sync_log.completed_at - sync_log.started_at).total_seconds())
            db.session.commit()
            
            print(f"✓ Synchronisation terminée: {total_created} créés, {total_updated} mis à jour, {total_failed} échecs")
            
        except Exception as e:
            print(f"✗ Erreur synchronisation: {e}")
            import traceback
            traceback.print_exc()
            sync_log.status = 'error'
            sync_log.error_message = str(e)
            sync_log.completed_at = datetime.utcnow()
            db.session.commit()

# ============================================================================
# HELPERS
# ============================================================================

def get_provider_service(provider):
    """Récupérer le service correspondant au provider"""
    if provider.slug == 'cj-dropshipping':
        return CJDropshippingProvider(provider)
    elif provider.slug == 'printify':
        return PrintifyProvider(provider)
    elif provider.slug == 'amazon':
        return AmazonProvider(provider)
    elif provider.slug == 'ebay':
        return EbayProvider(provider)
    else:
        raise Exception(f"Provider {provider.slug} non supporté")

def create_product_from_source(provider, product_data, mapping):
    """Créer un produit MPS depuis une source externe"""
    # Appliquer la marge
    price = float(product_data.get('price', 0)) * mapping.apply_markup
    compare_price = float(product_data.get('compare_price', 0)) * mapping.apply_markup
    
    # Gérer les images
    images = product_data.get('images', [])
    image_url = images[0] if images and len(images) > 0 else None
    
    # Générer un slug unique depuis le SKU et l'ID externe
    import re
    import unicodedata
    product_name = product_data.get('name', 'Produit sans nom')
    if isinstance(product_name, list):
        product_name = product_name[0] if product_name else 'Produit sans nom'
    
    # Créer un slug simple depuis le SKU ou l'ID externe
    sku = product_data.get('sku', '')
    external_id = str(product_data.get('external_id', ''))
    
    if sku:
        base_slug = sku.lower().replace('_', '-')
    else:
        base_slug = f"product-{external_id}"
    
    # Nettoyer le slug
    slug = re.sub(r'[^a-z0-9-]', '', base_slug)
    
    # Vérifier l'unicité
    counter = 1
    original_slug = slug
    while Product.query.filter_by(slug=slug).first():
        slug = f"{original_slug}-{counter}"
        counter += 1
    
    # Créer le produit
    product = Product(
        name=product_data.get('name', 'Produit sans nom'),
        slug=slug,
        description=product_data.get('description', ''),
        price=price,
        compare_price=compare_price,
        stock=int(product_data.get('stock', 0)),
        sku=product_data.get('sku', f"{provider.slug}-{product_data.get('external_id', 'unknown')}"),
        category_id=mapping.mps_category_id,
        image_url=image_url,
        is_active=True
    )
    
    db.session.add(product)
    db.session.flush()
    
    # Créer la source
    source = ProductSource(
        product_id=product.id,
        provider_id=provider.id,
        external_product_id=str(product_data.get('external_id', '')),
        external_price=float(product_data.get('price', 0)),
        external_stock=int(product_data.get('stock', 0)),
        external_currency=product_data.get('currency', 'USD'),
        sync_status='synced',
        last_synced_at=datetime.utcnow()
    )
    
    # Sauvegarder uniquement les données brutes sans les inclure récursivement
    raw_data = product_data.get('raw_data', {})
    if raw_data:
        source.set_raw_data(raw_data)
    
    db.session.add(source)
    db.session.commit()
    
    return product

def update_product_from_source(source, product_data, mapping):
    """Mettre à jour un produit depuis sa source"""
    product = source.product
    
    # Mettre à jour le prix avec la marge
    product.price = product_data['price'] * mapping.apply_markup
    product.stock = product_data['stock']
    
    # Mettre à jour la source
    source.external_price = product_data['price']
    source.external_stock = product_data['stock']
    source.sync_status = 'synced'
    source.last_synced_at = datetime.utcnow()
    source.set_raw_data(product_data.get('raw_data', {}))
    
    db.session.commit()
