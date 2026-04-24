"""
Routes pour la page FAQ
"""
from flask import Blueprint, render_template

faq_bp = Blueprint('faq', __name__)


@faq_bp.route('/faq')
def index():
    """Page FAQ - Questions fréquentes"""
    return render_template('pages/faq.html')
