"""
Routes admin pour la configuration de la tarification CJ
"""
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required
from models.category import Category
from models.product import Product
from services.pricing_service import PricingService
from extensions import db
import json

admin_pricing_bp = Blueprint('admin_pricing', __name__, url_prefix='/admin/pricing')

pricing_service = PricingService()


@admin_pricing_bp.route('/')
# @login_required  # Temporairement désactivé pour debug
def index():
    """Page de configuration de la tarification"""
    return render_template('admin/cj_pricing.html')


@admin_pricing_bp.route('/api/markups')
def get_markups():
    """Récupérer les marges configurées"""
    try:
        # Charger depuis le fichier de configuration
        import os
        config_file = 'instance/category_markups.json'
        
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
                return jsonify({
                    'success': True,
                    'default_markup': config.get('default_markup', 60),
                    'category_markups': config.get('category_markups', {})
                })
        else:
            return jsonify({
                'success': True,
                'default_markup': 60,
                'category_markups': {}
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@admin_pricing_bp.route('/api/analytics')
@login_required
def get_analytics():
    """Récupérer les analytics de tarification"""
    try:
        analytics = pricing_service.get_pricing_analytics()
        
        return jsonify({
            'success': True,
            'analytics': analytics
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@admin_pricing_bp.route('/api/save-markups', methods=['POST'])
@login_required
def save_markups():
    """Enregistrer les marges configurées"""
    try:
        data = request.get_json()
        
        default_markup = data.get('default_markup', 60)
        category_markups = data.get('category_markups', {})
        
        # Mettre à jour le service
        pricing_service.default_markup = float(default_markup)
        
        for category_name, markup in category_markups.items():
            pricing_service.set_category_markup(category_name, float(markup))
        
        # Sauvegarder dans un fichier de configuration
        config = {
            'default_markup': default_markup,
            'category_markups': category_markups
        }
        
        with open('config/pricing_config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        return jsonify({
            'success': True,
            'message': 'Marges enregistrées'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@admin_pricing_bp.route('/api/recalculate', methods=['POST'])
@login_required
def recalculate_prices():
    """Recalculer tous les prix des produits"""
    try:
        result = pricing_service.recalculate_all_prices()
        
        return jsonify({
            'success': result['success'],
            'total': result.get('total', 0),
            'updated': result.get('updated', 0),
            'message': result.get('message', '')
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@admin_pricing_bp.route('/api/category/<int:category_id>/recalculate', methods=['POST'])
@login_required
def recalculate_category_prices(category_id):
    """Recalculer les prix d'une catégorie"""
    try:
        result = pricing_service.recalculate_all_prices(category_id=category_id)
        
        return jsonify({
            'success': result['success'],
            'total': result.get('total', 0),
            'updated': result.get('updated', 0),
            'message': result.get('message', '')
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
