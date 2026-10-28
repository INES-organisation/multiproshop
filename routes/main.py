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

@main.route('/template-test')
def template_test():
    return render_template('pages/template_test.html')

@main.route('/promotions')
def promotions():
    return render_template('pages/promotions.html')

@main.route('/nouveautes')
def nouveautes():
    return render_template('pages/nouveautes.html')

@main.route('/abonnements')
def abonnements():
    return render_template('pages/abonnements.html')

@main.route('/encheres')
def encheres():
    return render_template('pages/encheres.html')

@main.route('/annonces')
def annonces():
    return render_template('pages/annonces.html')

@main.route('/blog')
def blog():
    return render_template('pages/blog.html')
