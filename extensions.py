from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_caching import Cache

db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
cache = Cache()


def personal_page():
    """Une page qui affiche le compte du visiteur ou un message flash ne passe pas par le cache :
    sinon le premier client connecté verrait son nom et son e-mail servis à tous les visiteurs."""
    from flask import session
    from flask_login import current_user
    return current_user.is_authenticated or bool(session.get('_flashes'))
