"""Dernières corrections mineures pour les erreurs de classification CJ"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import create_app
from models.product import Product
from models.category import Category
from extensions import db

app = create_app()

# (source_mps_ids, mots_clés, target_mps_id)
FIXES = [
    # Électronique -> Maison
    ([1], ['bookshelf', 'corner bookshelf'], 67),
    # Électronique -> Santé
    ([1], ['shoulder wrap', 'shoulder pad', 'blood pressure monitor'], 87),
    # Électronique -> Animalerie
    ([1], ['bird bath heater', 'poultry thermostatic'], 178),
    # Bricolage -> Maison
    ([152], ['egg beater', 'shoehorn', 'bidet sprayer', 'door stop',
             'desk toy blind box', 'raised garden bed', 'garden bed with trellis',
             'piercing jewelry diamond'], 67),
]

with app.app_context():
    total = 0
    for src_ids, keywords, target in FIXES:
        for src in src_ids:
            prods = Product.query.filter_by(category_id=src).filter(Product.cj_pid.isnot(None)).all()
            for p in prods:
                nl = p.name.lower()
                if any(kw in nl for kw in keywords):
                    old = db.session.get(Category, p.category_id)
                    new = db.session.get(Category, target)
                    print(f"  FIX: {p.name[:55]:<55} | {old.name} -> {new.name}")
                    p.category_id = target
                    total += 1
    
    db.session.commit()
    print(f"\nTotal corrigés: {total}")
    
    # Distribution finale
    from sqlalchemy import func
    print(f"\nDISTRIBUTION FINALE:")
    dist = Product.query.filter(Product.cj_pid.isnot(None)).with_entities(
        Product.category_id, func.count(Product.id)
    ).group_by(Product.category_id).all()
    for cat_id, count in sorted(dist, key=lambda x: x[1], reverse=True):
        cat = db.session.get(Category, cat_id) if cat_id else None
        print(f"  {cat.name if cat else 'AUCUNE':<35} : {count:>6}")
    print(f"  {'TOTAL':<35} : {sum(c for _,c in dist):>6}")
