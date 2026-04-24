"""
Gestionnaires d'erreurs personnalisés
"""
from flask import Blueprint, render_template, request
from werkzeug.exceptions import HTTPException

errors_bp = Blueprint('errors', __name__)

@errors_bp.app_errorhandler(404)
def not_found_error(error):
    """Page 404 - Page non trouvée"""
    return render_template('errors/404.html'), 404

@errors_bp.app_errorhandler(500)
def internal_error(error):
    """Page 500 - Erreur serveur"""
    from extensions import db
    db.session.rollback()  # Rollback en cas d'erreur DB
    return render_template('errors/500.html'), 500

@errors_bp.app_errorhandler(403)
def forbidden_error(error):
    """Page 403 - Accès interdit"""
    return render_template('errors/403.html'), 403

@errors_bp.app_errorhandler(400)
def bad_request_error(error):
    """Page 400 - Mauvaise requête"""
    return render_template('errors/400.html'), 400

@errors_bp.app_errorhandler(Exception)
def handle_exception(error):
    """Gestionnaire générique pour toutes les exceptions"""
    # Si c'est une HTTPException, on la laisse passer
    if isinstance(error, HTTPException):
        return error
    
    # Sinon, on traite comme une erreur 500
    from extensions import db
    db.session.rollback()
    
    # En production, logger l'erreur
    import logging
    logging.error(f'Unhandled exception: {error}', exc_info=True)
    
    return render_template('errors/500.html'), 500
