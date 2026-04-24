"""
Routes admin pour les pages CJ (catégories et produits)
"""
from flask import Blueprint, render_template, request
from flask_login import login_required

bp = Blueprint('admin_cj_pages', __name__, url_prefix='/admin/cj')


@bp.route('/categories')
def categories():
    """Page admin catégories CJ"""
    try:
        return render_template('admin/cj_categories.html')
    except Exception as e:
        return f"Erreur template: {str(e)}", 500


@bp.route('/products')
def products():
    """Page admin produits CJ"""
    try:
        category_id = request.args.get('category')
        return render_template('admin/cj_products.html', category_id=category_id)
    except Exception as e:
        return f"Erreur template: {str(e)}", 500
