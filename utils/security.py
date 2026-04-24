"""
Utilitaires de sécurité
"""
from functools import wraps
from flask import request, jsonify, abort
from datetime import datetime, timedelta
import hashlib

# Dictionnaire pour le rate limiting simple (en mémoire)
# En production, utilisez Redis
_rate_limit_store = {}

def rate_limit(max_requests=10, window_seconds=60):
    """
    Décorateur pour limiter le nombre de requêtes
    
    Args:
        max_requests: Nombre maximum de requêtes
        window_seconds: Fenêtre de temps en secondes
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Identifier le client (IP)
            client_id = request.remote_addr
            
            # Clé pour le stockage
            key = f"{f.__name__}:{client_id}"
            
            # Nettoyer les anciennes entrées
            now = datetime.utcnow()
            if key in _rate_limit_store:
                _rate_limit_store[key] = [
                    req_time for req_time in _rate_limit_store[key]
                    if now - req_time < timedelta(seconds=window_seconds)
                ]
            else:
                _rate_limit_store[key] = []
            
            # Vérifier la limite
            if len(_rate_limit_store[key]) >= max_requests:
                return jsonify({
                    'error': 'Trop de requêtes. Veuillez réessayer plus tard.',
                    'retry_after': window_seconds
                }), 429
            
            # Ajouter la requête actuelle
            _rate_limit_store[key].append(now)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def sanitize_filename(filename):
    """
    Nettoyer un nom de fichier pour éviter les injections
    
    Args:
        filename: Nom du fichier à nettoyer
    
    Returns:
        Nom de fichier sécurisé
    """
    import re
    import os
    
    # Garder seulement le nom de base
    filename = os.path.basename(filename)
    
    # Supprimer les caractères dangereux
    filename = re.sub(r'[^\w\s.-]', '', filename)
    
    # Limiter la longueur
    name, ext = os.path.splitext(filename)
    if len(name) > 100:
        name = name[:100]
    
    return name + ext


def generate_secure_token(length=32):
    """
    Générer un token sécurisé
    
    Args:
        length: Longueur du token
    
    Returns:
        Token hexadécimal
    """
    import secrets
    return secrets.token_hex(length)


def hash_password_secure(password, salt=None):
    """
    Hasher un mot de passe de manière sécurisée
    
    Args:
        password: Mot de passe en clair
        salt: Salt optionnel
    
    Returns:
        Tuple (hash, salt)
    """
    if salt is None:
        import secrets
        salt = secrets.token_hex(16)
    
    # Utiliser PBKDF2 avec SHA256
    import hashlib
    hash_obj = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000  # 100k itérations
    )
    
    return hash_obj.hex(), salt


def verify_password_secure(password, password_hash, salt):
    """
    Vérifier un mot de passe
    
    Args:
        password: Mot de passe en clair
        password_hash: Hash stocké
        salt: Salt utilisé
    
    Returns:
        True si le mot de passe est correct
    """
    new_hash, _ = hash_password_secure(password, salt)
    return new_hash == password_hash


def allowed_file(filename, allowed_extensions={'png', 'jpg', 'jpeg', 'gif', 'webp'}):
    """
    Vérifier si un fichier est autorisé
    
    Args:
        filename: Nom du fichier
        allowed_extensions: Extensions autorisées
    
    Returns:
        True si autorisé
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


def validate_email(email):
    """
    Valider une adresse email
    
    Args:
        email: Adresse email
    
    Returns:
        True si valide
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def sanitize_html(text):
    """
    Nettoyer le HTML pour éviter les XSS
    
    Args:
        text: Texte HTML
    
    Returns:
        Texte nettoyé
    """
    import html
    return html.escape(text)


def check_sql_injection(text):
    """
    Vérifier si un texte contient des patterns d'injection SQL
    
    Args:
        text: Texte à vérifier
    
    Returns:
        True si suspect
    """
    import re
    
    # Patterns suspects
    patterns = [
        r"(\bUNION\b.*\bSELECT\b)",
        r"(\bDROP\b.*\bTABLE\b)",
        r"(\bINSERT\b.*\bINTO\b)",
        r"(\bDELETE\b.*\bFROM\b)",
        r"(--)",
        r"(;.*--)",
        r"(\bOR\b.*=.*)",
        r"(\bAND\b.*=.*)"
    ]
    
    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    
    return False


def require_api_key(f):
    """
    Décorateur pour exiger une clé API
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            return jsonify({'error': 'Clé API manquante'}), 401
        
        # Vérifier la clé API (à implémenter selon votre logique)
        # if not validate_api_key(api_key):
        #     return jsonify({'error': 'Clé API invalide'}), 401
        
        return f(*args, **kwargs)
    return decorated_function
