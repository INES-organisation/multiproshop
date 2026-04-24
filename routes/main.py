from flask import Blueprint, render_template, current_app
from models.product import Product
from models.category import Category
from services.product_service import ProductService
from extensions import cache

main = Blueprint('main', __name__)

@main.route('/')
@cache.cached(timeout=300)  # Cache 5 minutes
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

@main.route('/contact')
def contact():
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
