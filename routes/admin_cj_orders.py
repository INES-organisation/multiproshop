"""
Routes admin pour la gestion des commandes CJ Dropshipping
"""
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from functools import wraps
from models.order import Order, OrderItem
from models.api_provider import ApiProvider
from services.api_providers.cj_dropshipping_optimized import CJDropshippingProvider
from services.cj_order_service import CjOrderService
from extensions import db
import logging

logger = logging.getLogger(__name__)

admin_cj_orders = Blueprint('admin_cj_orders', __name__, url_prefix='/admin/cj/orders')


def admin_required(f):
    """Décorateur pour vérifier que l'utilisateur est admin"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Accès refusé. Droits administrateur requis.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


def get_cj_order_service():
    """Récupérer une instance de CjOrderService"""
    try:
        provider = ApiProvider.query.filter_by(name='CJ Dropshipping', active=True).first()
        if not provider:
            return None
        
        cj_api = CJDropshippingProvider(provider)
        return CjOrderService(cj_api)
    except Exception as e:
        logger.error(f"Erreur get_cj_order_service: {e}")
        return None


@admin_cj_orders.route('/')
@admin_required
def list_orders():
    """Liste des commandes CJ"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 20
        status_filter = request.args.get('status', '')
        
        # Construire la requête
        query = Order.query.filter(Order.payment_status == 'paid')
        
        if status_filter:
            query = query.filter(Order.status == status_filter)
        
        # Pagination
        pagination = query.order_by(Order.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        orders = pagination.items
        
        # Statistiques
        stats = {
            'total': Order.query.filter(Order.payment_status == 'paid').count(),
            'pending': Order.query.filter(Order.status == 'pending', Order.payment_status == 'paid').count(),
            'processing': Order.query.filter(Order.status == 'processing').count(),
            'shipped': Order.query.filter(Order.status == 'shipped').count(),
            'delivered': Order.query.filter(Order.status == 'delivered').count(),
            'with_cj_id': Order.query.filter(Order.cj_order_id.isnot(None)).count()
        }
        
        return render_template('admin/cj_orders.html',
                             orders=orders,
                             pagination=pagination,
                             stats=stats,
                             status_filter=status_filter)
    
    except Exception as e:
        logger.error(f"Erreur list_orders: {e}")
        flash(f'Erreur: {str(e)}', 'error')
        return render_template('admin/cj_orders.html', orders=[], stats={})


@admin_cj_orders.route('/<int:order_id>')
@admin_required
def order_detail(order_id):
    """Détails d'une commande"""
    try:
        order = Order.query.get_or_404(order_id)
        
        # Récupérer les infos CJ si disponibles
        cj_info = None
        if order.cj_order_id:
            service = get_cj_order_service()
            if service:
                cj_info = service.get_order_status(order.cj_order_id)
        
        return render_template('admin/cj_order_detail.html',
                             order=order,
                             cj_info=cj_info)
    
    except Exception as e:
        logger.error(f"Erreur order_detail: {e}")
        flash(f'Erreur: {str(e)}', 'error')
        return redirect(url_for('admin_cj_orders.list_orders'))


@admin_cj_orders.route('/api/create/<int:order_id>', methods=['POST'])
@admin_required
def create_order(order_id):
    """Créer une commande sur CJ"""
    try:
        service = get_cj_order_service()
        if not service:
            return jsonify({
                'success': False,
                'message': 'Service CJ non disponible'
            }), 500
        
        result = service.create_cj_order(order_id)
        
        if result.get('success'):
            flash('Commande créée sur CJ avec succès', 'success')
        else:
            flash(f"Erreur: {result.get('message')}", 'error')
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Erreur create_order: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@admin_cj_orders.route('/api/sync/<int:order_id>', methods=['POST'])
@admin_required
def sync_order(order_id):
    """Synchroniser le statut d'une commande"""
    try:
        service = get_cj_order_service()
        if not service:
            return jsonify({
                'success': False,
                'message': 'Service CJ non disponible'
            }), 500
        
        result = service.sync_order_status(order_id)
        
        if result.get('success'):
            flash('Statut synchronisé avec succès', 'success')
        else:
            flash(f"Erreur: {result.get('message')}", 'error')
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Erreur sync_order: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@admin_cj_orders.route('/api/tracking/<int:order_id>', methods=['GET'])
@admin_required
def get_tracking(order_id):
    """Récupérer les informations de tracking"""
    try:
        order = Order.query.get_or_404(order_id)
        
        if not order.cj_order_id:
            return jsonify({
                'success': False,
                'message': 'Pas de commande CJ associée'
            }), 404
        
        service = get_cj_order_service()
        if not service:
            return jsonify({
                'success': False,
                'message': 'Service CJ non disponible'
            }), 500
        
        result = service.get_tracking_info(order.cj_order_id)
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Erreur get_tracking: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@admin_cj_orders.route('/api/cancel/<int:order_id>', methods=['POST'])
@admin_required
def cancel_order(order_id):
    """Annuler une commande CJ"""
    try:
        order = Order.query.get_or_404(order_id)
        
        if not order.cj_order_id:
            return jsonify({
                'success': False,
                'message': 'Pas de commande CJ à annuler'
            }), 404
        
        reason = request.json.get('reason', 'Admin cancellation')
        
        service = get_cj_order_service()
        if not service:
            return jsonify({
                'success': False,
                'message': 'Service CJ non disponible'
            }), 500
        
        result = service.cancel_cj_order(order.cj_order_id, reason)
        
        if result.get('success'):
            order.status = 'cancelled'
            db.session.commit()
            flash('Commande annulée avec succès', 'success')
        else:
            flash(f"Erreur: {result.get('message')}", 'error')
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Erreur cancel_order: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@admin_cj_orders.route('/api/sync-all', methods=['POST'])
@admin_required
def sync_all_orders():
    """Synchroniser toutes les commandes en attente"""
    try:
        service = get_cj_order_service()
        if not service:
            return jsonify({
                'success': False,
                'message': 'Service CJ non disponible'
            }), 500
        
        result = service.sync_all_pending_orders()
        
        if result.get('success'):
            flash(result.get('message'), 'success')
        else:
            flash(f"Erreur: {result.get('message')}", 'error')
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Erreur sync_all_orders: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@admin_cj_orders.route('/api/bulk-action', methods=['POST'])
@admin_required
def bulk_action():
    """Actions en masse sur les commandes"""
    try:
        data = request.json
        action = data.get('action')
        order_ids = data.get('order_ids', [])
        
        if not action or not order_ids:
            return jsonify({
                'success': False,
                'message': 'Action ou IDs manquants'
            }), 400
        
        service = get_cj_order_service()
        if not service:
            return jsonify({
                'success': False,
                'message': 'Service CJ non disponible'
            }), 500
        
        results = {
            'success': 0,
            'failed': 0,
            'details': []
        }
        
        for order_id in order_ids:
            if action == 'create':
                result = service.create_cj_order(order_id)
            elif action == 'sync':
                result = service.sync_order_status(order_id)
            else:
                continue
            
            if result.get('success'):
                results['success'] += 1
            else:
                results['failed'] += 1
            
            results['details'].append({
                'order_id': order_id,
                'result': result
            })
        
        message = f"{results['success']} réussies, {results['failed']} échouées"
        flash(message, 'success' if results['failed'] == 0 else 'warning')
        
        return jsonify({
            'success': True,
            'message': message,
            'results': results
        })
    
    except Exception as e:
        logger.error(f"Erreur bulk_action: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
