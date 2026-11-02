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
    from datetime import datetime, timedelta
    from sqlalchemy import func, or_
    from models.product import Product
    from models.user import User
    from models.order import Order, OrderItem
    from models.cart_reminder import CartReminder

    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    # Les commandes internes passées au prix coûtant ne comptent pas dans le CA
    paid = Order.query.filter(Order.payment_status == 'paid').filter(
        or_(Order.admin_notes.is_(None), ~Order.admin_notes.like('Commande interne admin%')))

    def revenue(q):
        return q.with_entities(func.coalesce(func.sum(Order.total_price), 0.0)).scalar() or 0.0

    paid_month = paid.filter(Order.created_at >= month_start)
    stats = {
        'revenue_total': revenue(paid),
        'revenue_month': revenue(paid_month),
        'orders_paid': paid.count(),
        'orders_month': paid_month.count(),
        'orders_pending': Order.query.filter(Order.payment_status == 'pending').count(),
        'to_send_cj': Order.query.filter(Order.payment_status == 'paid', Order.cj_order_id.is_(None),
                                         Order.status.notin_(['cancelled', 'delivered'])).count(),
        'products_online': Product.query.filter(Product.is_active == True, Product.published_at.isnot(None)).count(),
        'products_out': Product.query.filter(Product.is_active == True, Product.published_at.isnot(None),
                                             Product.stock <= 0).count(),
        'products_count': Product.query.count(),
        'users_count': User.query.count(),
        'users_month': User.query.filter(User.created_at >= month_start).count(),
        'carts_relaunched': CartReminder.query.filter(CartReminder.steps_sent > 0).count(),
        'carts_recovered': CartReminder.query.filter(CartReminder.completed_at.isnot(None)).count(),
    }
    stats['avg_basket'] = stats['revenue_total'] / stats['orders_paid'] if stats['orders_paid'] else 0.0

    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(8).all()
    top_products = (db.session.query(Product, func.sum(OrderItem.quantity).label('qty'),
                                     func.sum(OrderItem.quantity * OrderItem.price).label('ca'))
                    .join(OrderItem, OrderItem.product_id == Product.id)
                    .join(Order, Order.id == OrderItem.order_id)
                    .filter(Order.payment_status == 'paid', Order.created_at >= now - timedelta(days=30))
                    .group_by(Product.id).order_by(func.sum(OrderItem.quantity).desc()).limit(5).all())
    return render_template('admin/dashboard.html', stats=stats, recent_orders=recent_orders,
                           top_products=top_products, products_count=stats['products_count'],
                           users_count=stats['users_count'])

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
        # Produits en ligne : marge de la variante la moins rentable (chacune comparée à son coût)
        mi = product.margin_info() if product.is_active else None
        if mi:
            cost, margin = mi['cost'][0], mi['margin'][0]
        else:
            cost = product.cost_price
            margin = round(product.price - product.cost_price, 2) if product.cost_price else ''
        writer.writerow([
            product.id, product.name, product.category.name if product.category else '',
            f"{product.price:.2f}", f"{cost:.2f}" if cost else '', margin,
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
        # La catégorie choisie et toutes ses sous-catégories (les produits sont rangés au niveau le plus fin)
        ids, frontier = {category_id}, [category_id]
        while frontier:
            frontier = [c.id for c in Category.query.filter(Category.parent_id.in_(frontier)).all() if c.id not in ids]
            ids.update(frontier)
        query = query.filter(Product.category_id.in_(ids))
    
    if status == 'selection':
        query = query.filter(Product.is_active == True, Product.published_at.isnot(None))
    elif status == 'active':
        query = query.filter_by(is_active=True)
    elif status == 'inactive':
        query = query.filter_by(is_active=False)
    elif status == 'draft':  # jamais mis en ligne : candidats à la publication
        query = query.filter(Product.is_active == False, Product.published_at.is_(None))
    elif status == 'unpublished':  # déjà en ligne puis retirés
        query = query.filter(Product.is_active == False, Product.published_at.isnot(None))
    elif status == 'low_stock':  # comme les compteurs : produits en ligne seulement
        query = query.filter(Product.is_active == True, Product.stock > 0, Product.stock <= Product.low_stock_threshold)
    elif status == 'out_of_stock':
        query = query.filter(Product.is_active == True, Product.stock <= 0)
    elif status == 'low_margin':  # en ligne avec au moins une variante vendue sous 2 € de marge
        low_ids = [p.id for p in Product.query.filter_by(is_active=True).all()
                   if (lambda mi: mi is None or mi['margin'][0] < 2)(p.margin_info())]
        query = query.filter(Product.id.in_(low_ids or [0]))

    sorts = {
        'newest': Product.created_at.desc(), 'oldest': Product.created_at.asc(),
        'name': Product.name.asc(), 'price_asc': Product.price.asc(), 'price_desc': Product.price.desc(),
        'stock_asc': Product.stock.asc(), 'stock_desc': Product.stock.desc(),
        'published': Product.published_at.desc().nullslast(),
    }
    sort = request.args.get('sort', 'newest')
    if sort not in sorts:
        sort = 'newest'

    # Pagination
    products_paginated = query.order_by(sorts[sort], Product.id.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Catégories pour le filtre
    categories = Category.query.filter_by(level=1).order_by(Category.name).all()
    
    # Statistiques (stock bas et ruptures : produits en ligne seulement, les inactifs ne se vendent pas)
    total_products = Product.query.count()
    active_products = Product.query.filter_by(is_active=True).count()
    low_stock_products = Product.query.filter(Product.is_active == True, Product.stock <= Product.low_stock_threshold,
                                              Product.stock > 0).count()
    out_of_stock_products = Product.query.filter(Product.is_active == True, Product.stock <= 0).count()
    
    return render_template('admin/products.html',
                         products=products_paginated,
                         categories=categories,
                         search=search,
                         current_category=category_id,
                         current_status=status,
                         current_sort=sort,
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
            was_active, old_price = product.is_active, product.price
            product.price = float(request.form['price'])
            product.compare_price = float(request.form.get('compare_price', 0)) or None
            product.stock = int(request.form.get('stock', 0))
            product.category_id = int(request.form['category_id'])
            product.brand = request.form.get('brand', '')
            product.weight = float(request.form.get('weight', 0)) or None
            product.is_active = 'is_active' in request.form
            if product.is_active and not was_active:
                # Même contrôles que le bouton Publier ; un prix saisi à la main n'est pas remplacé par la grille
                problem = _publish_problem(product, reprice=abs((old_price or 0) - product.price) < 0.005)
                product.is_active = False
                if problem:
                    flash(f'Modifications enregistrées, mais produit non publié : {problem}', 'error')
                else:
                    from services.publication import go_live
                    if go_live(product) == 'queued':
                        flash('Claude rédige la fiche en français : le produit passera en ligne dans une minute environ.', 'info')
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
    if not product.is_active:
        problem = _publish_problem(product)
        if problem:
            db.session.commit()  # garder le stock et les tarifs relus chez CJ
            flash(f'« {product.name} » non activé : {problem}', 'error')
            return redirect(request.referrer if (request.referrer or '').find('/admin/') >= 0 else url_for('admin.products'))
    state = 'live'
    if product.is_active:
        product.is_active = False
    else:
        from services.publication import go_live
        state = go_live(product)
    
    try:
        db.session.commit()
        if state == 'queued':
            flash(f'« {product.name} » : vérifications CJ faites, Claude rédige la fiche en français. '
                  'Le produit passera en ligne dans une minute environ.', 'info')
        else:
            status = "activé" if product.is_active else "désactivé"
            flash(f'Produit "{product.name}" {status} !', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur: {str(e)}', 'error')
    
    from extensions import cache
    cache.delete('menu_category_ids')
    referrer = request.referrer or ''
    return redirect(referrer if '/admin/products' in referrer else url_for('admin.products'))


def _launch_prices(product):
    """Première mise en ligne : les prix aberrants de l'ancien catalogue (0,02 € ou 159 998 €, ou le coût CJ
    en dollars recopié comme prix) sont recalculés avec la marge de la catégorie. Un prix fixé à la main
    dans une fourchette raisonnable (1,1 à 8 fois le coût) est gardé."""
    from models.product_variant import ProductVariant
    from models.cart import cost_price
    from services.pricing_service import PricingService
    root = product.category
    while root is not None and root.parent_id:
        root = root.parent
    pricing = PricingService()
    markup = pricing.get_markup_for_category(root.name if root else None)
    sane = lambda price, cost: price and cost and cost * 1.1 <= price <= cost * 8
    prices = []
    for variant in ProductVariant.query.filter_by(product_id=product.id, active=True).all():
        cost = cost_price(product, variant)
        if not cost:
            continue
        current = variant.price or product.price
        if not sane(current, cost):
            variant.price = pricing.calculate_selling_price(cost, markup)
        prices.append(variant.price or product.price)
    if prices:
        product.price = min(prices)
    elif product.cost_price and not sane(product.price, product.cost_price):
        product.price = pricing.calculate_selling_price(product.cost_price, markup)
    if product.compare_price and product.compare_price <= product.price:
        product.compare_price = None


def _publish_problem(product, deadline=None, reprice=True):
    """Raison d'empêcher la mise en ligne, ou None.
    Produit CJ : stock relu chez CJ, livraison France et Réunion vérifiée, et à la première publication
    prix calculés avec la grille (services/publication.py). Autres produits : prix aberrants recalculés.
    Puis refus d'une vente à perte, d'un coût ou d'un prix inconnu."""
    if product.cj_pid:
        from services.publication import prepare
        problem = prepare(product, deadline, reprice=reprice)
        if problem:
            return problem
    elif product.published_at is None and reprice:
        _launch_prices(product)
    if not product.price or product.price <= 0:
        return 'prix de vente manquant.'
    mi = product.margin_info()
    if mi is None:
        return 'coût CJ inconnu, impossible de vérifier la marge.'
    if mi['margin'][0] <= 0:
        return 'au moins une variante active serait vendue à perte (%.2f €). Corrigez son prix ou désactivez-la.' % mi['margin'][0]
    return None


# --- Recherche CJ en temps réel : chercher, chiffrer (coût, marge, port), importer en brouillon ---

def _cj_api():
    from config import Config
    from services.api_providers.cj_dropshipping_optimized import CJDropshippingApiOptimized
    return CJDropshippingApiOptimized(email=Config.CJ_EMAIL, password=Config.CJ_PASSWORD, dev_key=Config.CJ_DEV_KEY)


def _cj_details(pid):
    """Fiche CJ complète (product/query), gardée 1 h : le chiffrage du port et l'import la relisent"""
    from extensions import cache
    key = f'cj_details:{pid}'
    details = cache.get(key)
    if details is None:
        details = _cj_api().get_product_details(pid)
        if details:
            cache.set(key, details, timeout=3600)
    return details


@admin_bp.route('/cj-recherche')
@login_required
@admin_required
def cj_search():
    """Recherche dans le catalogue CJ (product/listV2), avec le prix de vente que donnerait la marge"""
    from models.product import Product
    from services.pricing_service import PricingService
    from services.shipping_service import USD_TO_EUR
    q = request.args.get('q', '').strip()
    page = max(request.args.get('page', 1, type=int), 1)
    category_id = request.args.get('category', type=int)
    categories = Category.query.filter_by(level=1).order_by(Category.name).all()
    category = Category.query.get(category_id) if category_id else None
    root = category
    while root is not None and root.parent_id:
        root = root.parent
    results, total_pages = [], 0
    # Mot-clé, catégorie CJ, ou les deux : la catégorie filtre les résultats chez CJ (identifiant CJ de la
    # catégorie, ou à défaut celui de la table de correspondance category_mapping)
    cj_category, error = (_cj_category_for(category) if category else (None, None))
    if q or cj_category:
        data = _cj_api().get_products_v2(page=page, page_size=24, keyword=q or None, category_id=cj_category)
        total_pages = data.get('total_pages', 0)
        if not data.get('products') and data.get('total', 0) == 0 and page == 1 and not q:
            error = "CJ ne renvoie aucun produit pour cette catégorie seule : ajoutez un mot-clé."
        from services.publication import grid_price
        imported = {p.cj_pid: p for p in Product.query.filter(
            Product.cj_pid.in_([r['pid'] for r in data['products'] if r.get('pid')])).all()}
        for r in data['products']:
            cost = round(r['price'] * USD_TO_EUR, 2)
            price = grid_price(cost) if cost else 0  # le prix que donnera la publication
            results.append({**r, 'cost': cost, 'sell_price': price, 'margin': round(price - cost, 2),
                            'existing': imported.get(r['pid'])})
    elif category and not cj_category and not error:
        error = "Cette catégorie n'a pas d'équivalent CJ : ajoutez un mot-clé ou choisissez une sous-catégorie."
    if q and category and not cj_category:
        error = (error or '') + ' Résultats affichés sans filtre de catégorie.'
    return render_template('admin/cj_search.html', q=q, page=page, results=results, total_pages=total_pages,
                           categories=categories, category=category, error=error)


def _cj_category_for(category):
    """(identifiant de catégorie CJ, message) pour filtrer la recherche CJ sur une catégorie de la boutique.
    CJ n'accepte qu'un identifiant : celui de la catégorie, sinon sa correspondance, sinon celle de son
    unique sous-catégorie liée ; plusieurs possibles → on demande une sous-catégorie plus précise."""
    from models.api_provider import CategoryMapping
    if category.cj_category_id:
        return category.cj_category_id, None
    direct = CategoryMapping.query.filter_by(mps_category_id=category.id).first()
    if direct:
        return direct.external_category_id, None
    ids, frontier = set(), [category.id]
    while frontier:
        children = Category.query.filter(Category.parent_id.in_(frontier)).all()
        frontier = [c.id for c in children]
        ids.update(c.cj_category_id for c in children if c.cj_category_id)
        if frontier:
            ids.update(m.external_category_id for m in
                       CategoryMapping.query.filter(CategoryMapping.mps_category_id.in_(frontier)).all())
    if len(ids) == 1:
        return ids.pop(), None
    if ids:
        return None, "Catégorie trop large pour CJ : choisissez une sous-catégorie."
    return None, None

@admin_bp.route('/cj-recherche/port', methods=['POST'])
@login_required
@admin_required
def cj_search_freight():
    """Port le moins cher d'une unité (première variante) vers la France et La Réunion"""
    from flask import jsonify
    from services.shipping_service import ShippingService
    pid = (request.get_json(silent=True) or {}).get('pid', '')
    details = _cj_details(pid) if pid else None
    vid = next((v['vid'] for v in (details or {}).get('variants', []) if v.get('vid')), None)
    if not vid:
        return jsonify({'success': False, 'message': 'Produit ou variante introuvable chez CJ'}), 404
    service = ShippingService()
    result = {'success': True, 'variants': len(details.get('variants', []))}
    for country in ('FR', 'RE'):
        methods = service._cart_freight([{'cj_vid': vid, 'quantity': 1}], country, timeout=7 * 24 * 3600)
        result[country] = None if methods is None else (
            {'price': methods[0]['price'], 'days': methods[0]['delivery_time'], 'name': methods[0]['name']}
            if methods else False)
    return jsonify(result)


@admin_bp.route('/cj-recherche/importer', methods=['POST'])
@login_required
@admin_required
def cj_search_import():
    """Importe un produit CJ en brouillon (inactif) : on traduit et vérifie la fiche avant de l'activer"""
    from models.product import Product
    from services.cj_sync_service import CjSyncService
    from services.pricing_service import PricingService
    from services.shipping_service import USD_TO_EUR
    pid = request.form.get('pid', '').strip()
    category = Category.query.get(request.form.get('category_id', type=int) or 0)
    existing = Product.query.filter_by(cj_pid=pid).first() if pid else None
    if existing:
        flash('Ce produit est déjà dans la boutique.', 'info')
        return redirect(url_for('admin.edit_product', product_id=existing.id))
    details = _cj_details(pid) if pid else None
    if not details or not category:
        flash('Produit CJ introuvable ou catégorie manquante.', 'error')
        return redirect(url_for('admin.cj_search', q=request.form.get('q', '')))
    try:
        CjSyncService(_cj_api())._sync_product(dict(details, category_id=None))
        product = Product.query.filter_by(cj_pid=pid).first()
        cost = round((details.get('price') or 0) * USD_TO_EUR, 2)
        from services.publication import apply_grid
        product.category_id = category.id
        product.cost_price = cost or None
        apply_grid(product)  # mêmes prix que ceux de la publication
        product.is_active = False  # brouillon : activé depuis la liste une fois la fiche relue
        product.published_at = None
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f'Import impossible : {e}', 'error')
        return redirect(url_for('admin.cj_search', q=request.form.get('q', '')))
    flash('Produit importé en brouillon : traduisez le titre et la description, puis activez-le.', 'success')
    return redirect(url_for('admin.edit_product', product_id=product.id))


@admin_bp.route('/products/bulk', methods=['POST'])
@login_required
@admin_required
def bulk_products():
    """Actions groupées sur les produits cochés : activer (et publier), désactiver, changer de catégorie"""
    from models.product import Product
    ids = [int(i) for i in request.form.getlist('ids') if i.isdigit()]
    action = request.form.get('action')
    target = request.form.get('next') or url_for('admin.products')
    if not target.startswith('/admin/'):
        target = url_for('admin.products')
    if not ids or action not in ('activate', 'deactivate', 'category'):
        flash('Cochez au moins un produit et choisissez une action.', 'error')
        return redirect(target)
    products = Product.query.filter(Product.id.in_(ids)).all()
    if action == 'category':
        category = Category.query.get(request.form.get('category_id', type=int) or 0)
        if not category:
            flash('Choisissez la nouvelle catégorie.', 'error')
            return redirect(target)
        for p in products:
            p.category_id = category.id
        message = f'{len(products)} produit(s) déplacé(s) dans « {category.name} »'
    else:
        refused = []
        changed = 0
        queued = 0
        import time as _time
        deadline = _time.time() + 40  # chaque produit CJ coûte des appels CJ : rester sous le délai web
        for p in products:
            if action == 'activate' and not p.is_active:
                problem = _publish_problem(p, deadline)
                if problem:
                    refused.append(f'#{p.id} ({problem})')
                    continue
            if action == 'activate' and not p.is_active:
                from services.publication import go_live
                if go_live(p) == 'queued':
                    queued += 1
                    continue
            else:
                p.is_active = action == 'activate'
            changed += 1
        message = f"{changed} produit(s) {'activé(s)' if action == 'activate' else 'désactivé(s)'}"
        if queued:
            message += f" ; {queued} en cours de rédaction par Claude, en ligne d'ici quelques minutes"
        if refused:
            flash('Non activés : ' + ' ; '.join(refused[:10]) + (' …' if len(refused) > 10 else ''), 'error')
    db.session.commit()
    from extensions import cache
    cache.delete('menu_category_ids')  # le menu ne montre que les catégories avec des produits actifs
    flash(message, 'success')
    return redirect(target)


# ============================================================================
# CODES PROMO
# ============================================================================

def _parse_date(value, end_of_day=False):
    if not value:
        return None
    try:
        d = datetime.strptime(value, '%Y-%m-%d')
    except ValueError:
        return None
    return d.replace(hour=23, minute=59, second=59) if end_of_day else d


@admin_bp.route('/coupons', methods=['GET', 'POST'])
@login_required
@admin_required
def coupons():
    """Liste et création des codes promo"""
    from models.coupon import Coupon
    from models.order import Order
    from services.coupons import normalize

    if request.method == 'POST':
        f = request.form
        code = normalize(f.get('code'))
        kind = f.get('kind') if f.get('kind') in Coupon.KINDS else 'percent'
        try:
            value = float((f.get('value') or '0').replace(',', '.'))
            min_subtotal = float((f.get('min_subtotal') or '0').replace(',', '.'))
            max_uses = int(f['max_uses']) if f.get('max_uses') else None
        except ValueError:
            flash('Valeur, minimum ou nombre d\'utilisations invalide.', 'error')
            return redirect(url_for('admin.coupons'))
        if not code:
            flash('Indiquez un code.', 'error')
        elif Coupon.query.filter_by(code=code).first():
            flash(f'Le code {code} existe déjà.', 'error')
        elif kind == 'percent' and not 0 < value <= 90:
            flash('Le pourcentage doit être compris entre 1 et 90.', 'error')
        elif kind == 'fixed' and value <= 0:
            flash('Le montant doit être positif.', 'error')
        else:
            db.session.add(Coupon(
                code=code, kind=kind, value=value if kind != 'shipping' else 0, min_subtotal=max(min_subtotal, 0),
                starts_at=_parse_date(f.get('starts_at')), ends_at=_parse_date(f.get('ends_at'), True),
                max_uses=max_uses, once_per_email=bool(f.get('once_per_email')), note=(f.get('note') or '')[:200] or None,
            ))
            db.session.commit()
            flash(f'Code {code} créé.', 'success')
        return redirect(url_for('admin.coupons'))

    # Les codes de bienvenue personnels de la newsletter sont résumés à part
    items = Coupon.query.filter(db.or_(Coupon.note.is_(None), ~Coupon.note.like('newsletter %'))) \
        .order_by(Coupon.created_at.desc()).all()
    from models.newsletter import NewsletterSubscriber
    nl = {'subscribers': NewsletterSubscriber.query.filter(NewsletterSubscriber.unsubscribed_at.is_(None)).count(),
          'used': Coupon.query.filter(Coupon.note.like('newsletter %'), Coupon.uses > 0).count()}
    totals = dict(db.session.query(Order.coupon_code, db.func.sum(Order.discount_amount))
                  .filter(Order.payment_status == 'paid', Order.coupon_code.isnot(None))
                  .group_by(Order.coupon_code).all())
    return render_template('admin/coupons.html', coupons=items, kinds=Coupon.KINDS, totals=totals, nl=nl)


@admin_bp.route('/newsletter.csv')
@login_required
@admin_required
def newsletter_export():
    """Inscrits actifs à la newsletter (pour un outil d'envoi type Brevo)"""
    import csv
    import io
    from flask import Response
    from models.newsletter import NewsletterSubscriber
    out = io.StringIO()
    writer = csv.writer(out, delimiter=';')
    writer.writerow(['email', 'inscrit_le', 'source', 'code_bienvenue'])
    for sub in NewsletterSubscriber.query.filter(NewsletterSubscriber.unsubscribed_at.is_(None)) \
            .order_by(NewsletterSubscriber.created_at).all():
        writer.writerow([sub.email, sub.created_at.strftime('%Y-%m-%d') if sub.created_at else '', sub.source or '',
                         sub.coupon_code or ''])
    return Response('\ufeff' + out.getvalue(), mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=newsletter.csv'})


@admin_bp.route('/coupons/<int:coupon_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_coupon(coupon_id):
    from models.coupon import Coupon
    coupon = Coupon.query.get_or_404(coupon_id)
    coupon.active = not coupon.active
    db.session.commit()
    flash(f'Code {coupon.code} {"activé" if coupon.active else "désactivé"}.', 'success')
    return redirect(url_for('admin.coupons'))


@admin_bp.route('/coupons/<int:coupon_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_coupon(coupon_id):
    from models.coupon import Coupon
    coupon = Coupon.query.get_or_404(coupon_id)
    if coupon.uses:
        coupon.active = False
        flash(f'Code {coupon.code} déjà utilisé : désactivé plutôt que supprimé.', 'info')
    else:
        db.session.delete(coupon)
        flash(f'Code {coupon.code} supprimé.', 'success')
    db.session.commit()
    return redirect(url_for('admin.coupons'))


# ============================================================================
# NOTIFICATIONS ET LITIGES CJ
# ============================================================================

@admin_bp.route('/notifications', methods=['GET', 'POST'])
@login_required
@admin_required
def notifications():
    from models.admin_notification import AdminNotification
    from services.notifications import mark_read, KINDS
    if request.method == 'POST':
        ids = [int(i) for i in request.form.getlist('ids') if i.isdigit()]
        mark_read(ids or None)
        flash('Notifications marquées comme lues.', 'success')
        return redirect(url_for('admin.notifications', kind=request.args.get('kind') or None))
    kind = request.args.get('kind') or None
    q = AdminNotification.query
    if kind:
        q = q.filter_by(kind=kind)
    if request.args.get('unread'):
        q = q.filter_by(read_at=None)
    page = q.order_by(AdminNotification.created_at.desc()).paginate(page=request.args.get('page', 1, type=int),
                                                                     per_page=50, error_out=False)
    return render_template('admin/notifications.html', notifications=page, kinds=KINDS, kind=kind)


@admin_bp.route('/litiges')
@login_required
@admin_required
def disputes():
    """Litiges ouverts chez CJ, lus en direct"""
    from services import cj_disputes
    page = max(request.args.get('page', 1, type=int), 1)
    order_id = (request.args.get('order') or '').strip() or None
    data = cj_disputes.fetch(_cj_api(), page=page, size=20, order_id=order_id)
    return render_template('admin/disputes.html', data=data, page=page, order_id=order_id)
