"""Vérification finale de la distribution et échantillon par catégorie"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.product import Product
from models.category import Category
from sqlalchemy import func
from extensions import db

app = create_app()

with app.app_context():
    print("\n=== DISTRIBUTION FINALE ===\n")
    dist = Product.query.filter(Product.cj_pid.isnot(None)).with_entities(
        Product.category_id, func.count(Product.id)
    ).group_by(Product.category_id).all()
    
    total = 0
    for cat_id, count in sorted(dist, key=lambda x: x[1], reverse=True):
        cat = db.session.get(Category, cat_id) if cat_id else None
        name = cat.name if cat else 'AUCUNE'
        print(f"  {name:<35} : {count:>6}")
        total += count
    print(f"\n  {'TOTAL':<35} : {total:>6}")
    
    # Échantillon de chaque catégorie pour vérification visuelle
    print("\n=== ECHANTILLON PAR CATEGORIE ===\n")
    mps_ids = [1, 22, 38, 52, 67, 87, 100, 113, 126, 139, 152, 178]
    
    for mps_id in mps_ids:
        cat = db.session.get(Category, mps_id)
        if not cat:
            continue
        prods = Product.query.filter_by(category_id=mps_id).filter(
            Product.cj_pid.isnot(None)
        ).limit(8).all()
        
        count = Product.query.filter_by(category_id=mps_id).filter(
            Product.cj_pid.isnot(None)
        ).count()
        
        print(f"\n--- {cat.name} ({count} produits) ---")
        for p in prods:
            print(f"  {p.name[:75]}")
