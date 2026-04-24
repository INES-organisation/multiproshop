"""
Route de test pour vérifier l'affichage des catégories
"""
from flask import Blueprint, render_template
from extensions import db
from models.category import Category

test_bp = Blueprint('test', __name__, url_prefix='/test')

@test_bp.route('/categories')
def test_categories():
    """Page de test pour afficher les catégories"""
    
    from flask import current_app
    import os
    
    # Diagnostic du chemin de la BD
    db_uri = current_app.config['SQLALCHEMY_DATABASE_URI']
    db_path = db_uri.replace('sqlite:///', '')
    
    print(f"\n{'='*70}")
    print(f"🔍 DIAGNOSTIC BASE DE DONNÉES")
    print(f"{'='*70}")
    print(f"📍 DB URI: {db_uri}")
    print(f"📁 DB Path: {db_path}")
    print(f"✅ Fichier existe: {os.path.exists(db_path)}")
    if os.path.exists(db_path):
        print(f"📊 Taille fichier: {os.path.getsize(db_path)} bytes")
    print(f"{'='*70}")
    
    # Forcer le rechargement
    db.session.expire_all()
    
    # Récupérer toutes les catégories
    categories = Category.query.order_by(Category.id).all()
    
    # Debug dans la console
    print(f"🔍 TEST CATEGORIES - Nombre trouvé: {len(categories)}")
    print(f"{'='*70}")
    for cat in categories:
        print(f"   {cat.id:2d}. {cat.name}")
    print(f"{'='*70}\n")
    
    # Ajouter les infos de debug au template
    debug_info = {
        'db_uri': db_uri,
        'db_path': db_path,
        'db_exists': os.path.exists(db_path),
        'db_size': os.path.getsize(db_path) if os.path.exists(db_path) else 0
    }
    
    return render_template('test/categories_test.html', categories=categories, debug_info=debug_info)
