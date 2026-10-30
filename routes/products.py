from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from models.category import Category
from models.product import Product
from models.product_review import ProductReview
from services.product_service import ProductService
from extensions import cache, db, personal_page

products = Blueprint('products', __name__)

@products.route('/')
@cache.cached(timeout=300, query_string=True, unless=personal_page)  # Cache 5 min, visiteurs anonymes
def list_products():
    page = request.args.get('page', 1, type=int)
    per_page = 12
    sort_by = request.args.get('sort', 'name')
    category_id = request.args.get('category', type=int)
    
    products = ProductService.get_products_paginated(
        page=page,
        per_page=per_page,
        sort_by=sort_by,
        category_id=category_id
    )
    
    # Catégories pour la page (pas de cache memoize pour éviter DetachedInstanceError)
    categories = Category.query.filter_by(is_active=True, visible=True).all()
    main_categories = Category.query.filter_by(level=1, is_active=True, visible=True).order_by(Category.order, Category.name).all()
    
    return render_template('pages/list.html',
                         products=products,
                         categories=categories,
                         main_categories=main_categories,
                         current_category=category_id,
                         current_sort=sort_by)

@products.route('/search')
def search():
    """Redirection vers la nouvelle route de recherche"""
    query = request.args.get('q', '')
    return redirect(url_for('search.search', q=query))

@products.route('/category/<int:category_id>')
def category_products(category_id):
    from flask import jsonify
    
    category = Category.query.get_or_404(category_id)
    page = request.args.get('page', 1, type=int)
    per_page = 12
    
    pagination = ProductService.get_products_by_category(category_id, page=page, per_page=per_page)
    
    # Si requête AJAX, retourner JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        products_data = []
        for product in pagination.items:
            products_data.append({
                'id': product.id,
                'name': product.name,
                'price': product.price,
                'image_url': product.image_url,
                'category_name': product.category.name if product.category else ''
            })
        
        return jsonify({
            'success': True,
            'products': products_data,
            'has_more': pagination.has_next,
            'next_page': pagination.next_num if pagination.has_next else None
        })
    
    # Sinon, retourner le template HTML
    return render_template('pages/category_products.html',
                         category=category,
                         pagination=pagination,
                         products=pagination.items)

# Alias pour la sidebar
@products.route('/cat/<int:category_id>')
def by_category(category_id):
    return category_products(category_id)

@products.route('/<int:product_id>')
@cache.cached(timeout=600, unless=personal_page)  # Cache 10 minutes, visiteurs anonymes
def product_detail(product_id):
    product = ProductService.get_product_by_id(product_id)
    if not product or not product.is_active:  # produit retiré de la vente : plus de fiche
        flash('Produit introuvable', 'error')
        return redirect(url_for('products.list_products'))
    
    related_products = ProductService.get_related_products(product)
    
    # Utiliser le template CJ si le produit vient de CJ
    if product.cj_pid:
        return render_template('pages/product_detail_cj.html',
                             product=product,
                             related_products=related_products)
    
    return render_template('pages/product_detail.html',
                         product=product,
                         related_products=related_products)

@products.route('/api/<int:product_id>')
@cache.cached(timeout=600)
def get_product_api(product_id):
    """API pour récupérer les données complètes d'un produit"""
    try:
        product = Product.query.get(product_id)
        if not product:
            return jsonify({
                'success': False,
                'message': 'Produit introuvable'
            }), 404
        
        # Récupérer les images (à implémenter selon votre structure)
        images = []
        if product.image_url:
            images.append(product.image_url)
        
        # Ajouter les images des variantes si disponibles
        if hasattr(product, 'variants'):
            for variant in product.variants:
                if variant.image_url and variant.image_url not in images:
                    images.append(variant.image_url)
        
        return jsonify({
            'success': True,
            'product': {
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'price': float(product.price) if product.price else 0,
                'compare_price': float(product.compare_price) if product.compare_price else None,
                'cost_price': float(product.cost_price) if product.cost_price else None,
                'stock': product.stock,
                'sku': product.sku,
                'weight': product.weight,
                'image_url': product.image_url,
                'images': images,
                'category_id': product.category_id,
                'category_name': product.category.name if product.category else None,
                'cj_pid': product.cj_pid,
                'has_variants': hasattr(product, 'variants') and len(product.variants) > 0,
                'published': product.published,
                'is_active': product.is_active
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur: {str(e)}'
        }), 500
