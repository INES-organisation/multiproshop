"""
Service d'authentification
"""
from models.user import User
from extensions import db


class AuthService:
    """Service pour gérer l'authentification des utilisateurs"""
    
    @staticmethod
    def register_user(username, email, password):
        """
        Enregistre un nouvel utilisateur
        
        Args:
            username: Nom d'utilisateur
            email: Email de l'utilisateur
            password: Mot de passe
            
        Returns:
            tuple: (success: bool, message: str, user: User or None)
        """
        # Vérifier si l'utilisateur existe déjà
        user_exists = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if user_exists:
            return False, 'Un utilisateur avec ce nom ou cet email existe déjà', None
        
        # Créer le nouvel utilisateur
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        
        try:
            db.session.add(new_user)
            db.session.commit()
            return True, 'Inscription réussie', new_user
        except Exception as e:
            db.session.rollback()
            return False, f'Erreur lors de l\'inscription: {str(e)}', None
    
    @staticmethod
    def authenticate_user(identifiant, password):
        """
        Authentifie un utilisateur
        
        Args:
            identifiant: Username ou email
            password: Mot de passe
            
        Returns:
            tuple: (success: bool, message: str, user: User or None)
        """
        # Chercher l'utilisateur par username ou email
        user = User.query.filter(
            (User.username == identifiant) | (User.email == identifiant)
        ).first()
        
        if not user:
            return False, 'Utilisateur introuvable', None
        
        if not user.check_password(password):
            return False, 'Mot de passe incorrect', None
        
        return True, 'Authentification réussie', user
    
    @staticmethod
    def authenticate_admin(identifiant, password):
        """
        Authentifie un administrateur
        
        Args:
            identifiant: Username ou email
            password: Mot de passe
            
        Returns:
            tuple: (success: bool, message: str, user: User or None)
        """
        # Authentifier l'utilisateur
        success, message, user = AuthService.authenticate_user(identifiant, password)
        
        if not success:
            return False, message, None
        
        # Vérifier le rôle admin
        role_name = getattr(user.role, 'name', None)
        
        if role_name != 'admin':
            return False, 'Accès réservé aux administrateurs', None
        
        return True, 'Authentification admin réussie', user
    
    @staticmethod
    def check_user_exists(username=None, email=None):
        """
        Vérifie si un utilisateur existe
        
        Args:
            username: Nom d'utilisateur (optionnel)
            email: Email (optionnel)
            
        Returns:
            bool: True si l'utilisateur existe
        """
        if username and email:
            return User.query.filter(
                (User.username == username) | (User.email == email)
            ).first() is not None
        elif username:
            return User.query.filter_by(username=username).first() is not None
        elif email:
            return User.query.filter_by(email=email).first() is not None
        
        return False
