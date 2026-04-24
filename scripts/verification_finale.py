"""
Vérification finale complète de toutes les catégories MPS.
Affiche 8 produits par catégorie pour inspection visuelle.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.product import Product
from models.category import Category
from extensions import db
from sqlalchemy import func

app = create_app()

MPS_CATEGORIES = [
    (38, 'Téléphonie & Tablettes'),
    (22, 'Informatique'),
    (52, 'Mode & Vêtements'),
    (67, 'Maison & Jardin'),
    (87, 'Santé & Beauté'),
    (139, 'Auto & Moto'),
    (1, 'Électronique & High-Tech'),
    (178, 'Animalerie'),
    (100, 'Sports & Loisirs'),
    (126, 'Jeux & Jouets'),
    (152, 'Bricolage & Outillage'),
    (113, 'Bébés & Puériculture'),
]

with app.app_context():
    print("="*80)
    print("VÉRIFICATION FINALE COMPLÈTE")
    print("="*80)
    
    total = 0
    for cat_id, cat_name in MPS_CATEGORIES:
        count = Product.query.filter_by(category_id=cat_id).filter(
            Product.cj_pid.isnot(None)
        ).count()
        total += count
        
        prods = Product.query.filter_by(category_id=cat_id).filter(
            Product.cj_pid.isnot(None)
        ).order_by(func.random()).limit(8).all()
        
        print(f"\n{'─'*80}")
        print(f"  {cat_name} ({count} produits)")
        print(f"{'─'*80}")
        for p in prods:
            print(f"    {p.name[:72]}")
    
    print(f"\n{'='*80}")
    print(f"  TOTAL: {total} produits CJ")
    print(f"{'='*80}")
