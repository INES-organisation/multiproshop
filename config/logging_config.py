"""
Configuration du logging structuré
Phase 4 - Monitoring et logs
"""
import logging
import logging.handlers
import os
from pathlib import Path
import json
from datetime import datetime


class JSONFormatter(logging.Formatter):
    """Formatter pour logs en JSON"""
    
    def format(self, record):
        """Formater le log en JSON"""
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Ajouter les extras
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        
        if hasattr(record, 'ip_address'):
            log_data['ip_address'] = record.ip_address
        
        # Ajouter l'exception si présente
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


def setup_logging(app):
    """
    Configurer le logging pour l'application
    
    Args:
        app: Instance Flask
    """
    # Créer le dossier logs
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    # Niveau de log selon l'environnement
    if app.config.get('ENV') == 'production':
        log_level = logging.INFO
    else:
        log_level = logging.DEBUG
    
    # Configuration du logger racine
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Handler console (développement)
    if app.config.get('ENV') != 'production':
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
    
    # Handler fichier général
    file_handler = logging.handlers.RotatingFileHandler(
        log_dir / 'app.log',
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # Handler fichier erreurs
    error_handler = logging.handlers.RotatingFileHandler(
        log_dir / 'errors.log',
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    root_logger.addHandler(error_handler)
    
    # Handler JSON (production)
    if app.config.get('ENV') == 'production':
        json_handler = logging.handlers.RotatingFileHandler(
            log_dir / 'app.json.log',
            maxBytes=10485760,  # 10MB
            backupCount=10
        )
        json_handler.setLevel(logging.INFO)
        json_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(json_handler)
    
    # Logger spécifique pour les requêtes
    request_logger = logging.getLogger('requests')
    request_handler = logging.handlers.RotatingFileHandler(
        log_dir / 'requests.log',
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    request_handler.setLevel(logging.INFO)
    request_handler.setFormatter(file_formatter)
    request_logger.addHandler(request_handler)
    
    # Logger spécifique pour CJ API
    cj_logger = logging.getLogger('cj_api')
    cj_handler = logging.handlers.RotatingFileHandler(
        log_dir / 'cj_api.log',
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    cj_handler.setLevel(logging.INFO)
    cj_handler.setFormatter(file_formatter)
    cj_logger.addHandler(cj_handler)
    
    app.logger.info("Logging configuré")


def log_request(request, response=None, user_id=None):
    """
    Logger une requête HTTP
    
    Args:
        request: Objet request Flask
        response: Objet response Flask (optionnel)
        user_id: ID utilisateur (optionnel)
    """
    logger = logging.getLogger('requests')
    
    log_data = {
        'method': request.method,
        'path': request.path,
        'ip': request.remote_addr,
        'user_agent': request.user_agent.string
    }
    
    if user_id:
        log_data['user_id'] = user_id
    
    if response:
        log_data['status'] = response.status_code
        log_data['size'] = response.content_length
    
    logger.info(f"Request: {json.dumps(log_data)}")


def log_cj_api_call(endpoint, method='GET', params=None, response_code=None, error=None):
    """
    Logger un appel API CJ
    
    Args:
        endpoint: Endpoint appelé
        method: Méthode HTTP
        params: Paramètres de la requête
        response_code: Code de réponse
        error: Message d'erreur si échec
    """
    logger = logging.getLogger('cj_api')
    
    log_data = {
        'endpoint': endpoint,
        'method': method,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if params:
        log_data['params'] = params
    
    if response_code:
        log_data['response_code'] = response_code
    
    if error:
        log_data['error'] = error
        logger.error(f"CJ API Error: {json.dumps(log_data)}")
    else:
        logger.info(f"CJ API Call: {json.dumps(log_data)}")
