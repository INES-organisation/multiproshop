"""
Derniers ajustements :
1. Produits lingerie/sexy dans "Hauts & Ensembles Femme" -> "Lingerie & Sous-Vêtements Femme"
2. Produits massage dans "Rouleaux de massage" -> vérifier si c'est correct
3. Vider le cache
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.product import Product
from models.category import Category
from extensions import db

app = create_app()

with app.app_context():
    # 1. Trouver la catégorie Lingerie
    lingerie = Category.query.filter_by(name='Lingerie & Sous-Vêtements Femme').first()
    hauts_femme = Category.query.filter(
        Category.name == 'Hauts & Ensembles Femme',
        Category.level == 2
    ).first()
    
    print("--- 1. Lingerie mal classée dans Hauts & Ensembles Femme ---\n")
    
    if lingerie and hauts_femme:
        prods = Product.query.filter_by(category_id=hauts_femme.id).filter(
            Product.cj_pid.isnot(None)
        ).all()
        
        moved = 0
        for p in prods:
            nl = p.name.lower()
            is_lingerie = any(kw in nl for kw in [
                'sexy', 'lingerie', 'sheer', 'lace mesh', 'nightgown',
                'pajama', 'sleepwear', 'loungewear', 'thong', 'maid uniform',
                'belly band', 'transparent', 'hollow-out', 'camisole nightgown',
                'embroidery sheer', 'playful', 'passionate'
            ])
            if is_lingerie:
                p.category_id = lingerie.id
                print(f"  {p.name[:55]:<55} -> Lingerie")
                moved += 1
        
        db.session.commit()
        print(f"\n  Migrés: {moved}")
    
    # 2. Renommer "Rouleaux de massage" en "Massage & Relaxation" si c'est le cas
    print("\n--- 2. Vérifier catégorie massage ---\n")
    
    massage_cat = Category.query.filter(
        Category.name.ilike('%Rouleaux de massage%')
    ).first()
    
    if massage_cat:
        count = Product.query.filter_by(category_id=massage_cat.id).filter(
            Product.cj_pid.isnot(None)
        ).count()
        print(f"  '{massage_cat.name}' (ID:{massage_cat.id}): {count} produits")
        
        prods = Product.query.filter_by(category_id=massage_cat.id).filter(
            Product.cj_pid.isnot(None)
        ).all()
        for p in prods:
            print(f"    {p.name[:60]}")
        
        # Renommer en "Massage & Relaxation" si les produits sont des masseurs
        if count > 0:
            massage_cat.name = 'Massage & Relaxation'
            massage_cat.name_fr = 'Massage & Relaxation'
            db.session.commit()
            print(f"\n  Renommé en: Massage & Relaxation")
    
    # 3. Vérification rapide de la distribution
    print(f"\n--- 3. Distribution par catégorie MPS L1 ---\n")
    
    mps_l1 = Category.query.filter_by(level=1).filter(
        Category.cj_category_id.is_(None)
    ).order_by(Category.name).all()
    
    grand_total = 0
    for l1 in mps_l1:
        # Compter tous les produits dans cette branche
        total = 0
        
        # Direct L1
        total += Product.query.filter_by(category_id=l1.id).filter(
            Product.cj_pid.isnot(None)
        ).count()
        
        # L2
        l2s = Category.query.filter_by(parent_id=l1.id).all()
        for l2 in l2s:
            total += Product.query.filter_by(category_id=l2.id).filter(
                Product.cj_pid.isnot(None)
            ).count()
            # L3
            l3s = Category.query.filter_by(parent_id=l2.id).all()
            for l3 in l3s:
                total += Product.query.filter_by(category_id=l3.id).filter(
                    Product.cj_pid.isnot(None)
                ).count()
        
        if total > 0:
            print(f"  {l1.name:<35} : {total:>6}")
            grand_total += total
    
    print(f"  {'TOTAL':<35} : {grand_total:>6}")
