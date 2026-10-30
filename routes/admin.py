from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime
from extensions import db
from models.role import Role
from models.user import User
from models.category import Category

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Vous devez être connecté pour accéder à cette page.', 'warning')
            return redirect(url_for('auth.login'))
        
        role_name = getattr(current_user.role, 'name', None)
        if role_name != 'admin':
            flash('Accès réservé aux administrateurs.', 'error')
            return redirect(url_for('main.index'))
        
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    # Récupérer les statistiques
    from models.product import Product
    from models.user import User
    products_count = Product.query.count()
    users_count = User.query.count()
    return render_template('admin/dashboard.html', products_count=products_count, users_count=users_count)

@admin_bp.route('/users/export')
@login_required
@admin_required
def export_users():
    from models.user import User
    import csv
    from flask import Response
    users = User.query.all()
    def generate():
        data = [['ID', 'Nom', 'Email', 'Rôle', 'Date création']]
        for user in users:
            data.append([user.id, user.username, user.email, user.role.name if user.role else '', user.created_at.strftime('%d/%m/%Y')])
        for row in data:
            yield ','.join(str(cell) for cell in row) + '\n'
    return Response(generate(), mimetype='text/csv', headers={"Content-Disposition": "attachment;filename=utilisateurs.csv"})

@admin_bp.route('/users', methods=['GET'])
@login_required
@admin_required
def users():
    """Liste des utilisateurs"""
    from sqlalchemy import or_
    
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    role_filter = request.args.get('role', '')
    per_page = 20
    
    # Query de base
    query = User.query
    
    # Recherche
    if search:
        query = query.filter(
            or_(
                User.username.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%')
            )
        )
    
    # Filtre par rôle
    if role_filter:
        query = query.join(Role).filter(Role.name == role_filter)
    
    # Tri par date de création (plus récents en premier)
    query = query.order_by(User.id.desc())
    
    # Pagination
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Statistiques
    total_users = User.query.count()
    admin_count = User.query.join(Role).filter(Role.name == 'admin').count()
    client_count = User.query.join(Role).filter(Role.name == 'client').count()
    
    return render_template('admin/users.html',
                         users=pagination.items,
                         pagination=pagination,
                         total_users=total_users,
                         admin_count=admin_count,
                         client_count=client_count,
                         current_search=search,
                         current_role=role_filter)

@admin_bp.route('/users/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    roles = Role.query.all()
    if request.method == 'POST':
        from models.user import User
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role_id = request.form['role_id']
        if User.query.filter((User.username==username)|(User.email==email)).first():
            flash('Nom ou email déjà utilisé.')
            return render_template('admin/user_form.html', user=None, roles=roles)
        user = User(username=username, email=email, role_id=role_id)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Utilisateur créé avec succès.')
        return redirect(url_for('admin.users'))
    return render_template('admin/user_form.html', user=None, roles=roles)

@admin_bp.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    from models.user import User
    user = User.query.get_or_404(user_id)
    roles = Role.query.all()
    if request.method == 'POST':
        user.username = request.form['username']
        user.email = request.form['email']
        user.role_id = request.form['role_id']
        password = request.form['password']
        if password:
            user.set_password(password)
        db.session.commit()
        flash('Utilisateur mis à jour.')
        return redirect(url_for('admin.users'))
    return render_template('admin/user_form.html', user=user, roles=roles)

@admin_bp.route('/users/delete/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def delete_user(user_id):
    from models.user import User
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Vous ne pouvez pas supprimer votre propre compte.', 'error')
        return redirect(url_for('admin.users'))
    if request.method == 'POST':
        db.session.delete(user)
        db.session.commit()
        flash('Utilisateur supprimé.')
        return redirect(url_for('admin.users'))
    return render_template('admin/user_delete.html', user=user)

@admin_bp.route('/products/export')
@login_required
@admin_required
def export_products():
    from models.product import Product
    import csv
    from flask import Response
    import io
    from sqlalchemy.orm import joinedload
    # Construit en mémoire dans la requête : un générateur paresseux perdait la session SQLAlchemy
    out = io.StringIO()
    writer = csv.writer(out, delimiter=';')  # point-virgule : ouverture directe dans Excel en français
    writer.writerow(['ID', 'Nom', 'Catégorie', 'Prix de vente', 'Coût CJ', 'Marge', 'Marge %', 'Stock',
                     'Actif', 'Sélection', 'Réf. CJ', 'Lien'])
    for product in Product.query.options(joinedload(Product.category)).order_by(Product.id):
        margin = round(product.price - product.cost_price, 2) if product.cost_price else ''
        writer.writerow([
            product.id, product.name, product.category.name if product.category else '',
            f"{product.price:.2f}", f"{product.cost_price:.2f}" if product.cost_price else '', margin,
            f"{margin / product.price * 100:.0f}" if margin != '' and product.price else '',
            product.stock, 'oui' if product.is_active else 'non', 'oui' if product.published_at else 'non',
            product.cj_pid or '', url_for('products.product_detail', product_id=product.id, _external=True),
        ])
    return Response('\ufeff' + out.getvalue(), mimetype='text/csv; charset=utf-8',
                    headers={"Content-Disposition": "attachment;filename=produits.csv"})

# Anciennes routes produits supprimées - voir nouvelles routes en bas du fichier

@admin_bp.route('/categories/export')
@login_required
@admin_required
def export_categories():
    from models.category import Category
    import csv
    from flask import Response
    categories = Category.query.all()
    def generate():
        data = [['ID', 'Nom', 'Description']]
        for category in categories:
            data.append([
                category.id,
                category.name,
                category.description or ''
            ])
        for row in data:
            yield ','.join(str(cell) for cell in row) + '\n'
    return Response(generate(), mimetype='text/csv', headers={"Content-Disposition": "attachment;filename=categories.csv"})

@admin_bp.route('/categories', methods=['GET'])
@login_required
@admin_required
def categories():
    from models.category import Category
    
    # Forcer l'expiration de la session pour recharger les données
    db.session.expire_all()
    
    search = request.args.get('search','')
    level = request.args.get('level', type=int)
    
    # Requête de base
    q = Category.query
    
    # Filtrer par recherche
    if search:
        q = q.filter(Category.name.ilike(f'%{search}%'))
    
    # Filtrer par niveau
    if level:
        q = q.filter(Category.level == level)
    else:
        # Par défaut, afficher seulement les catégories principales
        q = q.filter(Category.level == 1)
    
    # Trier par ordre
    categories = q.order_by(Category.order, Category.name).all()
    
    # Statistiques
    stats = {
        'total': Category.query.count(),
        'level1': Category.query.filter_by(level=1).count(),
        'level2': Category.query.filter_by(level=2).count(),
        'level3': Category.query.filter_by(level=3).count()
    }
    
    return render_template('admin/categories_hierarchical.html', 
                         categories=categories, 
                         search=search, 
                         current_level=level or 1,
                         stats=stats)

@admin_bp.route('/categories/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_category():
    from models.category import Category
    from slugify import slugify
    
    if request.method == 'POST':
        name = request.form['name']
        description = request.form.get('description', '')
        parent_id = request.form.get('parent_id', type=int)
        icon = request.form.get('icon', 'fa-folder')
        
        # Déterminer le niveau
        if parent_id:
            parent = Category.query.get(parent_id)
            level = parent.level + 1 if parent else 1
        else:
            level = 1
        
        # Créer le slug
        slug = slugify(name)
        
        category = Category(
            name=name,
            slug=slug,
            description=description,
            parent_id=parent_id,
            level=level,
            icon=icon
        )
        db.session.add(category)
        db.session.commit()
        flash('Catégorie créée avec succès.', 'success')
        return redirect(url_for('admin.categories'))
    
    # Récupérer toutes les catégories pour le sélecteur parent
    all_categories = Category.query.order_by(Category.level, Category.name).all()
    return render_template('admin/category_form.html', category=None, all_categories=all_categories)

@admin_bp.route('/categories/edit/<int:category_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_category(category_id):
    from models.category import Category
    from slugify import slugify
    
    category = Category.query.get_or_404(category_id)
    
    if request.method == 'POST':
        category.name = request.form['name']
        category.description = request.form.get('description', '')
        category.icon = request.form.get('icon', 'fa-folder')
        parent_id = request.form.get('parent_id', type=int)
        
        # Mettre à jour le parent et le niveau
        if parent_id and parent_id != category.id:  # Éviter auto-référence
            parent = Category.query.get(parent_id)
            category.parent_id = parent_id
            category.level = parent.level + 1 if parent else 1
        elif not parent_id:
            category.parent_id = None
            category.level = 1
        
        # Mettre à jour le slug
        category.slug = slugify(category.name)
        
        db.session.commit()
        flash('Catégorie mise à jour avec succès.', 'success')
        return redirect(url_for('admin.categories'))
    
    # Récupérer toutes les catégories sauf celle en cours d'édition
    all_categories = Category.query.filter(Category.id != category_id).order_by(Category.level, Category.name).all()
    return render_template('admin/category_form.html', category=category, all_categories=all_categories)

@admin_bp.route('/categories/delete/<int:category_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def delete_category(category_id):
    from models.category import Category
    category = Category.query.get_or_404(category_id)
    if request.method == 'POST':
        db.session.delete(category)
        db.session.commit()
        flash('Catégorie supprimée.')
        return redirect(url_for('admin.categories'))
    return render_template('pages/admin/category_delete.html', category=category)

@admin_bp.route('/orders', methods=['GET'])
@login_required
@admin_required
def orders():
    """Liste des commandes avec filtres et pagination"""
    from models.order import Order
    from sqlalchemy import or_, desc
    from sqlalchemy.orm import joinedload, selectinload
    
    # Récupérer les paramètres de recherche et filtres
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    status_filter = request.args.get('status', '')
    payment_status_filter = request.args.get('payment_status', '')
    sort = request.args.get('sort', 'newest')
    
    # Query de base avec eager loading
    query = Order.query.options(joinedload(Order.user), selectinload(Order.order_items))
    
    # Recherche
    if search:
        query = query.filter(
            or_(
                Order.order_number.ilike(f'%{search}%'),
                Order.customer_email.ilike(f'%{search}%'),
                Order.shipping_first_name.ilike(f'%{search}%'),
                Order.shipping_last_name.ilike(f'%{search}%')
            )
        )
    
    # Filtres
    if status_filter:
        query = query.filter(Order.status == status_filter)
    
    if payment_status_filter:
        query = query.filter(Order.payment_status == payment_status_filter)
    
    # Tri
    if sort == 'newest':
        query = query.order_by(desc(Order.created_at))
    elif sort == 'oldest':
        query = query.order_by(Order.created_at)
    elif sort == 'highest':
        query = query.order_by(desc(Order.total_price))
    elif sort == 'lowest':
        query = query.order_by(Order.total_price)
    
    # Pagination
    orders = query.paginate(page=page, per_page=20, error_out=False)
    
    # Statistiques
    total_orders = Order.query.count()
    pending_orders = Order.query.filter_by(status='pending').count()
    processing_orders = Order.query.filter_by(status='processing').count()
    shipped_orders = Order.query.filter_by(status='shipped').count()
    total_revenue = db.session.query(db.func.sum(Order.total_price)).filter(Order.payment_status == 'paid').scalar() or 0
    
    return render_template('admin/orders.html',
                         orders=orders,
                         total_orders=total_orders,
                         pending_orders=pending_orders,
                         processing_orders=processing_orders,
                         shipped_orders=shipped_orders,
                         total_revenue=total_revenue,
                         current_search=search,
                         current_status=status_filter,
                         current_payment_status=payment_status_filter,
                         current_sort=sort)

@admin_bp.route('/orders/<int:order_id>')
@login_required
@admin_required
def order_detail(order_id):
    """Détails d'une commande"""
    from models.order import Order
    order = Order.query.get_or_404(order_id)
    return render_template('admin/order_detail.html', order=order)

@admin_bp.route('/orders/<int:order_id>/update-status', methods=['POST'])
@login_required
@admin_required
def update_order_status(order_id):
    """Mettre à jour le statut d'une commande"""
    from models.order import Order
    from datetime import datetime
    
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')
    admin_notes = request.form.get('admin_notes', '')
    
    if new_status:
        order.status = new_status
        
        # Mettre à jour les dates selon le statut
        if new_status == 'paid':
            order.payment_status = 'paid'
            order.paid_at = datetime.utcnow()
        elif new_status == 'shipped':
            order.shipped_at = datetime.utcnow()
        elif new_status == 'delivered':
            order.delivered_at = datetime.utcnow()
        
        if admin_notes:
            order.admin_notes = admin_notes
        
        db.session.commit()
        
        # Envoyer un email selon le nouveau statut
        try:
            if new_status == 'shipped':
                from utils.email import send_order_shipped_email
                send_order_shipped_email(order)
            elif new_status == 'delivered':
                from utils.email import send_order_delivered_email
                send_order_delivered_email(order)
        except Exception as e:
            print(f"Erreur envoi email: {e}")
        
        flash(f'Statut de la commande {order.order_number} mis à jour avec succès', 'success')
    
    return redirect(url_for('admin.order_detail', order_id=order_id))

@admin_bp.route('/orders/<int:order_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_order(order_id):
    """Supprimer une commande"""
    from models.order import Order
    
    order = Order.query.get_or_404(order_id)
    order_number = order.order_number
    
    db.session.delete(order)
    db.session.commit()
    
    flash(f'Commande {order_number} supprimée avec succès', 'success')
    return redirect(url_for('admin.orders'))

@admin_bp.route('/orders/export')
@login_required
@admin_required
def export_orders():
    """Exporter les commandes en CSV"""
    from models.order import Order
    import csv
    from io import StringIO
    from flask import Response
    
    orders = Order.query.order_by(Order.created_at.desc()).all()
    
    # Créer le CSV
    si = StringIO()
    writer = csv.writer(si)
    
    # En-têtes
    writer.writerow([
        'Numéro Commande', 'Date', 'Client', 'Email', 'Téléphone',
        'Sous-total', 'Livraison', 'TVA', 'Total',
        'Statut', 'Statut Paiement', 'Méthode Paiement',
        'Adresse', 'Ville', 'Code Postal', 'Pays'
    ])
    
    # Données
    for order in orders:
        writer.writerow([
            order.order_number,
            order.created_at.strftime('%d/%m/%Y %H:%M'),
            f"{order.shipping_first_name} {order.shipping_last_name}",
            order.customer_email,
            order.customer_phone or '',
            f"{order.subtotal:.2f}",
            f"{order.shipping_cost:.2f}",
            f"{order.tax:.2f}",
            f"{order.total_price:.2f}",
            order.status,
            order.payment_status,
            order.payment_method or '',
            order.shipping_address,
            order.shipping_city,
            order.shipping_postal_code,
            order.shipping_country
        ])
    
    output = si.getvalue()
    si.close()
    
    return Response(
        output,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment;filename=commandes_{datetime.now().strftime("%Y%m%d")}.csv'}
    )

# Routes promotions commentées - modèle promotion n'existe pas
# @admin_bp.route('/promotions/export')
# @login_required
# @admin_required
# def export_promotions():
#     from models.promotion import Promotion
#     import csv
#     from flask import Response
#     promotions = Promotion.query.all()
#     def generate():
#         data = [['ID', 'Titre', 'Description', 'Réduction', 'Début', 'Fin']]
#         for promo in promotions:
#             data.append([
#                 promo.id,
#                 promo.title,
#                 promo.description or '',
#                 promo.discount,
#                 promo.start_date.strftime('%d/%m/%Y') if promo.start_date else '',
#                 promo.end_date.strftime('%d/%m/%Y') if promo.end_date else ''
#             ])
#         for row in data:
#             yield ','.join(str(cell) for cell in row) + '\n'
#     return Response(generate(), mimetype='text/csv', headers={"Content-Disposition": "attachment;filename=promotions.csv"})

# @admin_bp.route('/promotions', methods=['GET'])
# @login_required
# @admin_required
# def promotions():
#     from models.promotion import Promotion
#     search = request.args.get('search','')
#     q = Promotion.query
#     if search:
#         q = q.filter((Promotion.title.ilike(f'%{search}%')) | (Promotion.description.ilike(f'%{search}%')))
#     promotions = q.all()
#     return render_template('pages/admin/promotions.html', promotions=promotions, search=search)

# @admin_bp.route('/promotions/create', methods=['GET', 'POST'])
# @login_required
# @admin_required
# def create_promotion():
#     from models.promotion import Promotion
#     from datetime import datetime
#     if request.method == 'POST':
#         title = request.form['title']
#         description = request.form['description']
#         discount = request.form['discount']
#         start_date = request.form['start_date'] or None
#         end_date = request.form['end_date'] or None
#         promo = Promotion(
#             title=title,
#             description=description,
#             discount=discount,
#             start_date=datetime.strptime(start_date, '%Y-%m-%d') if start_date else None,
#             end_date=datetime.strptime(end_date, '%Y-%m-%d') if end_date else None
#         )
#         db.session.add(promo)
#         db.session.commit()
#         flash('Promotion créée avec succès.')
#         return redirect(url_for('admin.promotions'))
#     return render_template('pages/admin/promotion_form.html', promotion=None)

# @admin_bp.route('/promotions/edit/<int:promotion_id>', methods=['GET', 'POST'])
# @login_required
# @admin_required
# def edit_promotion(promotion_id):
#     from models.promotion import Promotion
#     from datetime import datetime
#     promo = Promotion.query.get_or_404(promotion_id)
#     if request.method == 'POST':
#         promo.title = request.form['title']
#         promo.description = request.form['description']
#         promo.discount = request.form['discount']
#         start_date = request.form['start_date'] or None
#         end_date = request.form['end_date'] or None
#         promo.start_date = datetime.strptime(start_date, '%Y-%m-%d') if start_date else None
#         promo.end_date = datetime.strptime(end_date, '%Y-%m-%d') if end_date else None
#         db.session.commit()
#         flash('Promotion mise à jour.')
#         return redirect(url_for('admin.promotions'))
#     return render_template('pages/admin/promotion_form.html', promotion=promo)

# @admin_bp.route('/promotions/delete/<int:promotion_id>', methods=['GET', 'POST'])
# @login_required
# @admin_required
# def delete_promotion(promotion_id):
#     from models.promotion import Promotion
#     promo = Promotion.query.get_or_404(promotion_id)
#     if request.method == 'POST':
#         db.session.delete(promo)
#         db.session.commit()
#         flash('Promotion supprimée.')
#         return redirect(url_for('admin.promotions'))
#     return render_template('pages/admin/promotion_delete.html', promotion=promo)

# ============================================================================
# GESTION DES PRODUITS
# ============================================================================

@admin_bp.route('/products', methods=['GET'])
@login_required
@admin_required
def products():
    """Liste des produits avec filtres et recherche"""
    from models.product import Product
    from models.category import Category
    from sqlalchemy.orm import joinedload
    
    # Paramètres de recherche et filtrage
    search = request.args.get('search', '')
    category_id = request.args.get('category', type=int)
    status = request.args.get('status', '')
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Construction de la requête avec eager loading
    query = Product.query.options(joinedload(Product.category))
    
    if search:
        query = query.filter(
            (Product.name.ilike(f'%{search}%')) | 
            (Product.sku.ilike(f'%{search}%')) |
            (Product.brand.ilike(f'%{search}%'))
        )
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    if status == 'active':
        query = query.filter_by(is_active=True)
    elif status == 'inactive':
        query = query.filter_by(is_active=False)
    elif status == 'low_stock':
        query = query.filter(Product.stock <= Product.low_stock_threshold)
    elif status == 'out_of_stock':
        query = query.filter_by(stock=0)
    
    # Pagination
    products_paginated = query.order_by(Product.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Catégories pour le filtre
    categories = Category.query.filter_by(level=1).order_by(Category.name).all()
    
    # Statistiques
    total_products = Product.query.count()
    active_products = Product.query.filter_by(is_active=True).count()
    low_stock_products = Product.query.filter(Product.stock <= Product.low_stock_threshold, Product.stock > 0).count()
    out_of_stock_products = Product.query.filter_by(stock=0).count()
    
    return render_template('admin/products.html',
                         products=products_paginated,
                         categories=categories,
                         search=search,
                         current_category=category_id,
                         current_status=status,
                         total_products=total_products,
                         active_products=active_products,
                         low_stock_products=low_stock_products,
                         out_of_stock_products=out_of_stock_products)

@admin_bp.route('/products/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_product():
    """Créer un nouveau produit"""
    from models.product import Product
    from models.category import Category
    from slugify import slugify
    from werkzeug.utils import secure_filename
    import os
    
    categories = Category.query.order_by(Category.name).all()
    
    if request.method == 'POST':
        try:
            # Récupérer les données du formulaire
            name = request.form['name']
            slug = slugify(name)
            sku = request.form.get('sku', '')
            description = request.form.get('description', '')
            short_description = request.form.get('short_description', '')
            price = float(request.form['price'])
            compare_price = float(request.form.get('compare_price', 0)) or None
            stock = int(request.form.get('stock', 0))
            category_id = int(request.form['category_id'])
            brand = request.form.get('brand', '')
            weight = float(request.form.get('weight', 0)) or None
            is_active = 'is_active' in request.form
            is_featured = 'is_featured' in request.form
            is_new = 'is_new' in request.form
            
            # Créer le produit
            product = Product(
                name=name,
                slug=slug,
                sku=sku,
                description=description,
                short_description=short_description,
                price=price,
                compare_price=compare_price,
                stock=stock,
                category_id=category_id,
                brand=brand,
                weight=weight,
                is_active=is_active,
                is_featured=is_featured,
                is_new=is_new
            )
            
            # Gérer l'upload de l'image principale
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    # Créer le dossier uploads si nécessaire
                    upload_folder = os.path.join('static', 'uploads', 'products')
                    os.makedirs(upload_folder, exist_ok=True)
                    
                    # Sauvegarder le fichier
                    filepath = os.path.join(upload_folder, filename)
                    file.save(filepath)
                    product.image_url = f'/static/uploads/products/{filename}'
            
            db.session.add(product)
            db.session.commit()
            
            flash(f'Produit "{product.name}" créé avec succès !', 'success')
            return redirect(url_for('admin.products'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la création du produit: {str(e)}', 'error')
    
    return render_template('admin/product_form.html', product=None, categories=categories)

@admin_bp.route('/products/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_product(product_id):
    """Modifier un produit existant"""
    from models.product import Product
    from models.category import Category
    from slugify import slugify
    from werkzeug.utils import secure_filename
    import os
    
    product = Product.query.get_or_404(product_id)
    categories = Category.query.order_by(Category.name).all()
    
    if request.method == 'POST':
        try:
            # Mettre à jour les données
            product.name = request.form['name']
            product.slug = slugify(product.name)
            product.sku = request.form.get('sku', '')
            product.description = request.form.get('description', '')
            product.short_description = request.form.get('short_description', '')
            product.price = float(request.form['price'])
            product.compare_price = float(request.form.get('compare_price', 0)) or None
            product.stock = int(request.form.get('stock', 0))
            product.category_id = int(request.form['category_id'])
            product.brand = request.form.get('brand', '')
            product.weight = float(request.form.get('weight', 0)) or None
            product.is_active = 'is_active' in request.form
            product.is_featured = 'is_featured' in request.form
            product.is_new = 'is_new' in request.form
            
            # Gérer l'upload de la nouvelle image
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    upload_folder = os.path.join('static', 'uploads', 'products')
                    os.makedirs(upload_folder, exist_ok=True)
                    filepath = os.path.join(upload_folder, filename)
                    file.save(filepath)
                    product.image_url = f'/static/uploads/products/{filename}'
            
            db.session.commit()
            flash(f'Produit "{product.name}" modifié avec succès !', 'success')
            return redirect(url_for('admin.products'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la modification: {str(e)}', 'error')
    
    return render_template('admin/product_form.html', product=product, categories=categories)

@admin_bp.route('/products/delete/<int:product_id>', methods=['POST'])
@login_required
@admin_required
def delete_product(product_id):
    """Supprimer un produit"""
    from models.product import Product
    
    product = Product.query.get_or_404(product_id)
    product_name = product.name
    
    try:
        db.session.delete(product)
        db.session.commit()
        flash(f'Produit "{product_name}" supprimé avec succès !', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression: {str(e)}', 'error')
    
    return redirect(url_for('admin.products'))

@admin_bp.route('/products/toggle-status/<int:product_id>', methods=['POST'])
@login_required
@admin_required
def toggle_product_status(product_id):
    """Activer/désactiver un produit"""
    from models.product import Product
    
    product = Product.query.get_or_404(product_id)
    product.is_active = not product.is_active
    
    try:
        db.session.commit()
        status = "activé" if product.is_active else "désactivé"
        flash(f'Produit "{product.name}" {status} !', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur: {str(e)}', 'error')
    
    return redirect(url_for('admin.products'))
