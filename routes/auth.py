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

@auth.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        # Ici tu pourrais envoyer un email de réinitialisation si tu as une logique d'envoi de mail
        flash("Si un compte existe pour cet email, un lien de réinitialisation a été envoyé.")
        return redirect(url_for('auth.login'))
    return render_template('pages/forgot_password.html')
