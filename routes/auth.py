from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from services.auth_service import AuthService

auth = Blueprint('auth', __name__, url_prefix='/auth')

@auth.route('/inscription', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        success, message, user = AuthService.register_user(username, email, password)
        
        if success:
            flash(message + ' Connectez-vous!')
            return redirect(url_for('auth.login'))
        else:
            flash(message)
            return redirect(url_for('auth.register'))
    
    return render_template('pages/register.html')

@auth.route('/connexion', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifiant = request.form.get('username')
        password = request.form.get('password')
        
        success, message, user = AuthService.authenticate_user(identifiant, password)
        
        if success:
            login_user(user)
            return redirect(url_for('main.index'))
        else:
            flash(message)
    
    return render_template('pages/login.html')

@auth.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        identifiant = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember', False)
        
        success, message, user = AuthService.authenticate_admin(identifiant, password)
        
        if success:
            login_user(user, remember=True)  # Toujours remember pour admin
            from flask import session
            session.permanent = True  # Marquer la session comme permanente
            return redirect(url_for('admin.dashboard'))
        else:
            flash(message)
    
    return render_template('pages/admin_login.html')

@auth.route('/deconnexion')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@auth.route('/profil')
@login_required
def profile():
    return render_template('pages/profile.html')

RESET_MAX_AGE = 3600  # lien de réinitialisation valable 1 h


def _reset_serializer():
    from flask import current_app
    from itsdangerous import URLSafeTimedSerializer
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'], salt='reset-password')


def _reset_token(user):
    # L'empreinte du mot de passe actuel rend le lien inutilisable une fois le mot de passe changé
    return _reset_serializer().dumps({'id': user.id, 'h': user.password_hash[-12:]})


@auth.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        from models.user import User
        from utils.email import send_email
        email = (request.form.get('email') or '').strip()
        user = User.query.filter(User.email.ilike(email)).first() if email else None
        if user:
            link = url_for('auth.reset_password', token=_reset_token(user), _external=True)
            send_email(to=user.email, subject='Réinitialisation de votre mot de passe - MultiProShop',
                       html=render_template('emails/reset_password.html', user=user, link=link))
        # Même message dans tous les cas : ne pas révéler quelles adresses ont un compte
        flash("Si un compte existe pour cet email, un lien de réinitialisation vient d'être envoyé. Il est valable 1 heure.")
        return redirect(url_for('auth.login'))
    return render_template('pages/forgot_password.html')


@auth.route('/reinitialiser/<token>', methods=['GET', 'POST'])
def reset_password(token):
    from itsdangerous import BadSignature, SignatureExpired
    from models.user import User
    from extensions import db
    try:
        data = _reset_serializer().loads(token, max_age=RESET_MAX_AGE)
    except (SignatureExpired, BadSignature):
        data = None
    user = User.query.get(data['id']) if data else None
    if not user or user.password_hash[-12:] != data['h']:
        flash('Ce lien de réinitialisation est invalide ou a expiré. Demandez-en un nouveau.', 'error')
        return redirect(url_for('auth.forgot_password'))
    if request.method == 'POST':
        password = request.form.get('password') or ''
        if len(password) < 8:
            flash('Le mot de passe doit contenir au moins 8 caractères.', 'error')
        elif password != request.form.get('password_confirm'):
            flash('Les deux mots de passe ne correspondent pas.', 'error')
        else:
            user.set_password(password)
            db.session.commit()
            flash('Votre mot de passe a été modifié. Vous pouvez vous connecter.', 'success')
            return redirect(url_for('auth.login'))
    return render_template('pages/reset_password.html')
