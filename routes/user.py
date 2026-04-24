"""
Routes utilisateur pour le profil et les commandes
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models.order import Order
from sqlalchemy import desc

user_bp = Blueprint('user', __name__, url_prefix='/user')

@user_bp.route('/profile')
@login_required
def profile():
    """Page profil utilisateur"""
    return render_template('user/profile.html', user=current_user)

@user_bp.route('/orders')
@login_required
def orders():
    """Liste des commandes de l'utilisateur"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    
    # Query de base
    query = Order.query.filter_by(user_id=current_user.id)
    
    # Filtre par statut
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    # Tri par date décroissante
    query = query.order_by(desc(Order.created_at))
    
    # Pagination
    orders = query.paginate(page=page, per_page=10, error_out=False)
    
    # Statistiques utilisateur
    total_orders = Order.query.filter_by(user_id=current_user.id).count()
    total_spent = sum([o.total_price for o in Order.query.filter_by(user_id=current_user.id, payment_status='paid').all()])
    pending_orders = Order.query.filter_by(user_id=current_user.id, status='pending').count()
    
    return render_template('user/orders.html',
                         orders=orders,
                         total_orders=total_orders,
                         total_spent=total_spent,
                         pending_orders=pending_orders,
                         current_status=status_filter)

@user_bp.route('/orders/<int:order_id>')
@login_required
def order_detail(order_id):
    """Détails d'une commande utilisateur"""
    order = Order.query.get_or_404(order_id)
    
    # Vérifier que la commande appartient à l'utilisateur
    if order.user_id != current_user.id:
        flash('Accès non autorisé', 'error')
        return redirect(url_for('user.orders'))
    
    return render_template('user/order_detail.html', order=order)

@user_bp.route('/orders/<int:order_id>/cancel', methods=['POST'])
@login_required
def cancel_order(order_id):
    """Annuler une commande"""
    from extensions import db
    
    order = Order.query.get_or_404(order_id)
    
    # Vérifier que la commande appartient à l'utilisateur
    if order.user_id != current_user.id:
        flash('Accès non autorisé', 'error')
        return redirect(url_for('user.orders'))
    
    # Vérifier que la commande peut être annulée
    if order.status in ['shipped', 'delivered']:
        flash('Cette commande ne peut plus être annulée', 'error')
        return redirect(url_for('user.order_detail', order_id=order_id))
    
    # Annuler la commande
    order.status = 'cancelled'
    
    # Remettre les produits en stock
    for item in order.order_items:
        item.product.stock += item.quantity
    
    db.session.commit()
    
    flash(f'Commande {order.order_number} annulée avec succès', 'success')
    return redirect(url_for('user.order_detail', order_id=order_id))
