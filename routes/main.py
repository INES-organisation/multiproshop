from flask import Blueprint, render_template, current_app, request, flash, redirect, url_for
from models.product import Product
from models.category import Category
from services.product_service import ProductService
from extensions import cache, personal_page

main = Blueprint('main', __name__)

@main.route('/')
@cache.cached(timeout=300, unless=personal_page)  # Cache 5 minutes, visiteurs anonymes
def index():
    # Produits en vedette (les 8 premiers)
    featured_products = ProductService.get_featured_products()
    
    # Toutes les catégories (exclure les catégories CJ)
    categories = Category.query.filter_by(is_active=True, visible=True).all()
    
    # Deals du jour (produits récents)
    deals_of_the_day = ProductService.get_deals_of_the_day()
    
    # Suggestions personnalisées (produits aléatoires)
    suggestions = ProductService.get_suggestions()
    
    # Nouveautés (derniers produits ajoutés)
    new_arrivals = ProductService.get_new_arrivals()
    
    return render_template('pages/index.html', 
                         featured_products=featured_products,
                         categories=categories,
                         deals_of_the_day=deals_of_the_day,
                         suggestions=suggestions,
                         new_arrivals=new_arrivals)

@main.route('/about')
def about():
    return render_template('pages/about.html')

@main.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        from html import escape
        from utils.email import _send_via_ines

        form = {k: (request.form.get(k) or '').strip() for k in ('name', 'email', 'phone', 'subject', 'message', 'website')}
        if form['website']:  # champ invisible : rempli seulement par les robots
            return redirect(url_for('main.contact'))
        if not (form['name'] and form['email'] and form['message']):
            flash("Merci d'indiquer votre nom, votre e-mail et votre message.", 'error')
            return redirect(url_for('main.contact'))
        seller = current_app.config['SELLER']
        html = ''.join(f'<p><strong>{label} :</strong> {escape(form[key])}</p>' for key, label in (
            ('name', 'Nom'), ('email', 'E-mail'), ('phone', 'Téléphone'), ('subject', 'Sujet'))) \
            + '<p>' + escape(form['message']).replace('\n', '<br>') + '</p>'
        if _send_via_ines(seller['email'], f"[MultiProShop] Contact : {form['subject'] or 'question'} ({form['name']})", html):
            flash('Message envoyé, merci ! Nous vous répondons sous 48 h ouvrées.', 'success')
        else:
            flash(f"Votre message n'a pas pu être envoyé. Écrivez-nous directement à {seller['email']}.", 'error')
        return redirect(url_for('main.contact'))
    return render_template('pages/contact.html')

@main.route('/terms')
def terms():
    return render_template('pages/terms.html')

@main.route('/privacy')
def privacy():
    return render_template('pages/privacy.html')

@main.route('/legal')
def legal():
    return render_template('pages/legal.html')

@main.route('/confidentialite')
def confidentialite():
    return render_template('pages/confidentialite.html')

@main.route('/suivi-commande', methods=['GET', 'POST'])
def order_tracking():
    """Suivi sans compte : numéro de commande + e-mail de la commande"""
    from models.order import Order
    order = None
    if request.method == 'POST':
        number = (request.form.get('order_number') or '').strip().upper()
        email = (request.form.get('email') or '').strip().lower()
        if number and email:
            order = Order.query.filter_by(order_number=number).first()
            if order and order.customer_email.strip().lower() != email:
                order = None
        if not order:
            flash("Aucune commande ne correspond à ce numéro et à cet e-mail.", 'error')
    return render_template('pages/order_tracking.html', order=order)

# Anciennes pages de démonstration (contenu fictif) : redirigées vers le catalogue
@main.route('/promotions')
@main.route('/abonnements')
@main.route('/encheres')
@main.route('/annonces')
@main.route('/blog')
def retired_page():
    return redirect(url_for('products.list_products'), 301)

@main.route('/nouveautes')
def nouveautes():
    return redirect(url_for('products.list_products', sort='newest'), 301)
