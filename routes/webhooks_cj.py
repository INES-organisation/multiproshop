"""
Routes pour les webhooks CJ Dropshipping
Réception et traitement des notifications en temps réel
"""
from flask import Blueprint, request, jsonify
import logging
import json

logger = logging.getLogger(__name__)

webhooks_cj = Blueprint('webhooks_cj', __name__, url_prefix='/webhooks/cj')


@webhooks_cj.route('/message', methods=['POST'])
def webhook_message():
    """
    Endpoint principal pour les webhooks CJ (format réel)
    
    Format CJ:
    {
        "messageId": "unique_id",
        "type": "ORDER|STOCK|LOGISTIC|PRODUCT|VARIANT|ORDERSPLIT",
        "messageType": "UPDATE",
        "params": {...}
    }
    
    Types supportés :
    - ORDER: Mise à jour commande
    - STOCK: Mise à jour stock
    - LOGISTIC: Mise à jour tracking
    - PRODUCT: Mise à jour produit
    - VARIANT: Mise à jour variante
    - ORDERSPLIT: Division commande
    """
    try:
        # Récupérer les données (format JSON uniquement)
        if not request.is_json:
            logger.error("❌ Content-Type doit être application/json")
            return jsonify({
                'success': False,
                'error': 'Content-Type doit être application/json'
            }), 400
        
        data = request.get_json()
        
        logger.info(f"📥 Webhook CJ reçu")
        logger.debug(f"Data: {json.dumps(data, indent=2)}")
        
        # Vérifier le format
        message_id = data.get('messageId')
        message_type = data.get('type')
        
        if not message_id or not message_type:
            logger.error("❌ Format webhook invalide")
            return jsonify({
                'success': False,
                'error': 'messageId et type requis'
            }), 400
        
        # Traiter le webhook
        from services.webhook_handler import WebhookHandler
        handler = WebhookHandler()
        
        result = handler.process_webhook(data)
        
        # Logger le webhook
        handler.log_webhook(message_type, data, result)
        
        # CJ attend une réponse 200 OK en < 3 secondes
        return jsonify({
            'success': True,
            'message': 'Webhook reçu et traité'
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Erreur traitement webhook: {e}")
        import traceback
        traceback.print_exc()
        # Retourner 200 quand même pour éviter les retry CJ
        return jsonify({
            'success': True,
            'message': 'Webhook reçu (erreur interne)'
        }), 200




@webhooks_cj.route('/test', methods=['GET', 'POST'])
def webhook_test():
    """
    Endpoint de test pour vérifier que les webhooks fonctionnent
    
    Usage:
        curl -X POST http://localhost:5000/webhooks/cj/test \
             -H "Content-Type: application/json" \
             -d '{"test": "data"}'
    """
    try:
        logger.info(f"🧪 Test webhook reçu")
        
        data = {}
        if request.method == 'POST':
            if request.is_json:
                data = request.get_json()
            else:
                data = request.form.to_dict()
        
        return jsonify({
            'success': True,
            'message': 'Webhook test reçu avec succès',
            'method': request.method,
            'headers': dict(request.headers),
            'data': data,
            'timestamp': str(datetime.utcnow())
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Erreur test webhook: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@webhooks_cj.route('/logs', methods=['GET'])
def webhook_logs():
    """
    Afficher les logs des webhooks reçus
    
    Query params:
        - limit: Nombre de logs à afficher (défaut: 50)
        - event_type: Filtrer par type d'événement
        - success: Filtrer par succès (true/false)
    """
    try:
        from models.webhook_log import WebhookLog
        from flask_login import login_required, current_user
        
        # Vérifier que l'utilisateur est admin
        if not current_user.is_authenticated or current_user.role != 'admin':
            return jsonify({
                'success': False,
                'error': 'Accès non autorisé'
            }), 403
        
        # Paramètres de requête
        limit = request.args.get('limit', 50, type=int)
        event_type = request.args.get('event_type')
        success_filter = request.args.get('success')
        
        # Construire la requête
        query = WebhookLog.query
        
        if event_type:
            query = query.filter_by(event_type=event_type)
        
        if success_filter is not None:
            success_bool = success_filter.lower() == 'true'
            query = query.filter_by(success=success_bool)
        
        # Récupérer les logs
        logs = query.order_by(WebhookLog.created_at.desc()).limit(limit).all()
        
        # Formater les résultats
        results = []
        for log in logs:
            results.append({
                'id': log.id,
                'event_type': log.event_type,
                'success': log.success,
                'payload': json.loads(log.payload) if log.payload else {},
                'result': json.loads(log.result) if log.result else {},
                'created_at': log.created_at.isoformat()
            })
        
        return jsonify({
            'success': True,
            'count': len(results),
            'logs': results
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Erreur récupération logs: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@webhooks_cj.route('/stats', methods=['GET'])
def webhook_stats():
    """
    Statistiques sur les webhooks reçus
    """
    try:
        from models.webhook_log import WebhookLog
        from flask_login import login_required, current_user
        from sqlalchemy import func
        
        # Vérifier que l'utilisateur est admin
        if not current_user.is_authenticated or current_user.role != 'admin':
            return jsonify({
                'success': False,
                'error': 'Accès non autorisé'
            }), 403
        
        # Statistiques globales
        total = WebhookLog.query.count()
        success_count = WebhookLog.query.filter_by(success=True).count()
        error_count = WebhookLog.query.filter_by(success=False).count()
        
        # Statistiques par type d'événement
        event_stats = db.session.query(
            WebhookLog.event_type,
            func.count(WebhookLog.id).label('count'),
            func.sum(func.cast(WebhookLog.success, db.Integer)).label('success_count')
        ).group_by(WebhookLog.event_type).all()
        
        event_breakdown = []
        for event_type, count, success_count in event_stats:
            event_breakdown.append({
                'event_type': event_type,
                'total': count,
                'success': success_count or 0,
                'errors': count - (success_count or 0)
            })
        
        # Derniers webhooks
        recent = WebhookLog.query.order_by(
            WebhookLog.created_at.desc()
        ).limit(10).all()
        
        recent_list = []
        for log in recent:
            recent_list.append({
                'event_type': log.event_type,
                'success': log.success,
                'created_at': log.created_at.isoformat()
            })
        
        return jsonify({
            'success': True,
            'stats': {
                'total': total,
                'success': success_count,
                'errors': error_count,
                'success_rate': round(success_count / total * 100, 2) if total > 0 else 0
            },
            'by_event': event_breakdown,
            'recent': recent_list
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Erreur récupération stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Import nécessaire pour les routes
from datetime import datetime
from extensions import db
