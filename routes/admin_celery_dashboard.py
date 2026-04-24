"""
Dashboard Admin pour monitoring et contrôle Celery en temps réel
"""
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required
from celery_app import celery
from models.product import Product
from models.product_variant import ProductVariant
from extensions import db
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('admin_celery', __name__, url_prefix='/admin/celery')


@bp.route('/dashboard')
@login_required
def dashboard():
    """
    Dashboard principal Celery avec monitoring temps réel
    """
    return render_template('admin/celery_dashboard.html')


@bp.route('/api/status')
@login_required
def get_status():
    """
    Obtenir le statut global du système Celery
    GET /admin/celery/api/status
    """
    try:
        # IMPORTANT: Avec pool=solo sous Windows, les APIs d'inspection Celery
        # (stats, active, ping) ne fonctionnent pas. On vérifie directement Redis.
        
        workers_active = False
        worker_count = 0
        worker_names = []
        stats = None  # Initialiser stats pour éviter l'erreur
        
        try:
            # Vérifier directement dans Redis si des workers sont enregistrés
            import redis
            redis_client = redis.from_url('redis://localhost:6379/0')
            
            # Celery enregistre les workers dans Redis avec des clés spécifiques
            # Pattern: celery@hostname ou _kombu.binding.*
            keys = redis_client.keys('_kombu.binding.celery*')
            
            if keys and len(keys) > 0:
                workers_active = True
                worker_count = 1  # Au moins un worker est connecté
                worker_names = ['celery@worker']
            
            redis_client.close()
        except Exception as e:
            logger.warning(f"[Admin Celery] Impossible de vérifier Redis: {e}")
        
        # Fallback: Essayer quand même l'API d'inspection (peut fonctionner parfois)
        if not workers_active:
            try:
                inspect = celery.control.inspect(timeout=1.0)
                stats = inspect.stats()
                if stats and len(stats) > 0:
                    workers_active = True
                    worker_count = len(stats)
                    worker_names = list(stats.keys())
            except:
                pass
        
        # Statistiques base de données
        total_products = Product.query.filter(
            Product.cj_pid.isnot(None),
            Product.published == True
        ).count()
        
        products_with_variants = Product.query.join(ProductVariant).distinct().count()
        total_variants = ProductVariant.query.count()
        
        products_without_variants = total_products - products_with_variants
        
        return jsonify({
            'success': True,
            'celery': {
                'active': workers_active,
                'workers': worker_names,
                'worker_count': worker_count,
                'stats': stats
            },
            'database': {
                'total_products': total_products,
                'products_with_variants': products_with_variants,
                'products_without_variants': products_without_variants,
                'total_variants': total_variants,
                'completion_rate': round(products_with_variants / total_products * 100, 1) if total_products > 0 else 0
            }
        })
        
    except Exception as e:
        logger.error(f"[Admin Celery] Erreur get_status: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'celery': {
                'active': False,
                'workers': [],
                'worker_count': 0
            }
        })


@bp.route('/api/tasks/active')
@login_required
def get_active_tasks():
    """
    Obtenir la liste des tâches en cours d'exécution
    GET /admin/celery/api/tasks/active
    """
    try:
        inspect = celery.control.inspect()
        active = inspect.active()
        scheduled = inspect.scheduled()
        reserved = inspect.reserved()
        
        tasks = {
            'active': active or {},
            'scheduled': scheduled or {},
            'reserved': reserved or {},
            'total_active': sum(len(tasks) for tasks in (active or {}).values()),
            'total_scheduled': sum(len(tasks) for tasks in (scheduled or {}).values()),
            'total_reserved': sum(len(tasks) for tasks in (reserved or {}).values())
        }
        
        return jsonify({
            'success': True,
            'tasks': tasks
        })
        
    except Exception as e:
        logger.error(f"[Admin Celery] Erreur get_active_tasks: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })


@bp.route('/api/tasks/start', methods=['POST'])
@login_required
def start_task():
    """
    Démarrer une tâche de synchronisation
    POST /admin/celery/api/tasks/start
    Body: {
        "task": "sync_missing_variants" | "sync_all_variants" | "update_stock",
        "params": {...}
    }
    """
    try:
        data = request.get_json()
        task_name = data.get('task')
        params = data.get('params', {})
        
        if task_name == 'sync_missing_variants':
            result = celery.send_task('tasks.variant_sync_tasks.sync_missing_variants')
            task_id = result.id
            message = "Synchronisation des produits manquants lancée"
            
        elif task_name == 'sync_all_variants':
            batch_size = params.get('batch_size', 50)
            delay = params.get('delay', 600)
            result = celery.send_task(
                'tasks.variant_sync_tasks.sync_all_variants',
                args=[batch_size, delay]
            )
            task_id = result.id
            message = f"Synchronisation complète lancée (lots de {batch_size}, délai {delay}s)"
            
        elif task_name == 'update_stock':
            result = celery.send_task('tasks.variant_sync_tasks.update_stock_from_variants')
            task_id = result.id
            message = "Mise à jour des stocks lancée"
            
        else:
            return jsonify({
                'success': False,
                'error': f"Tâche inconnue: {task_name}"
            }), 400
        
        logger.info(f"[Admin Celery] Tâche lancée: {task_name} (ID: {task_id})")
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'task_name': task_name,
            'message': message
        })
        
    except Exception as e:
        logger.error(f"[Admin Celery] Erreur start_task: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/tasks/<task_id>/status')
@login_required
def get_task_status(task_id):
    """
    Obtenir le statut d'une tâche spécifique
    GET /admin/celery/api/tasks/<task_id>/status
    """
    try:
        from celery.result import AsyncResult
        
        result = AsyncResult(task_id, app=celery)
        
        response = {
            'success': True,
            'task_id': task_id,
            'state': result.state,
            'ready': result.ready(),
            'successful': result.successful() if result.ready() else None,
            'failed': result.failed() if result.ready() else None
        }
        
        if result.ready():
            if result.successful():
                response['result'] = result.result
            elif result.failed():
                response['error'] = str(result.info)
        else:
            response['info'] = str(result.info) if result.info else None
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"[Admin Celery] Erreur get_task_status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })


@bp.route('/api/tasks/<task_id>/revoke', methods=['POST'])
@login_required
def revoke_task(task_id):
    """
    Annuler une tâche en cours
    POST /admin/celery/api/tasks/<task_id>/revoke
    """
    try:
        celery.control.revoke(task_id, terminate=True)
        
        logger.info(f"[Admin Celery] Tâche annulée: {task_id}")
        
        return jsonify({
            'success': True,
            'message': f"Tâche {task_id} annulée"
        })
        
    except Exception as e:
        logger.error(f"[Admin Celery] Erreur revoke_task: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/workers/shutdown', methods=['POST'])
@login_required
def shutdown_workers():
    """
    Arrêter tous les workers Celery
    POST /admin/celery/api/workers/shutdown
    """
    try:
        celery.control.shutdown()
        
        logger.warning("[Admin Celery] Arrêt de tous les workers demandé")
        
        return jsonify({
            'success': True,
            'message': "Arrêt des workers en cours..."
        })
        
    except Exception as e:
        logger.error(f"[Admin Celery] Erreur shutdown_workers: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/queue/purge', methods=['POST'])
@login_required
def purge_queue():
    """
    Vider la file d'attente des tâches
    POST /admin/celery/api/queue/purge
    """
    try:
        celery.control.purge()
        
        logger.warning("[Admin Celery] File d'attente purgée")
        
        return jsonify({
            'success': True,
            'message': "File d'attente vidée"
        })
        
    except Exception as e:
        logger.error(f"[Admin Celery] Erreur purge_queue: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
