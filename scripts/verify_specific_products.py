"""Vérifier des produits spécifiques après le remapping final"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import create_app
from models.product import Product
from models.category import Category
from extensions import db

app = create_app()

with app.app_context():
    # Produit de la capture : Lingerie Bodysuit
    print("=== Produit Lingerie Bodysuit (ID 388) ===")
    p = db.session.get(Product, 388)
    if p:
        cat = db.session.get(Category, p.category_id) if p.category_id else None
        print(f"  Nom: {p.name}")
        print(f"  Catégorie: {cat.name if cat else 'AUCUNE'} (ID: {p.category_id})")
    
    # Produit Dual Monitor
    print("\n=== Produit Dual Monitor ===")
    p2 = Product.query.filter(Product.name.ilike('%dual monitor%')).first()
    if p2:
        cat2 = db.session.get(Category, p2.category_id) if p2.category_id else None
        print(f"  Nom: {p2.name}")
        print(f"  Catégorie: {cat2.name if cat2 else 'AUCUNE'} (ID: {p2.category_id})")
    
    # Vérifier qu'aucun produit lingerie/bra/underwear n'est dans Électronique
    print("\n=== Produits lingerie/bra dans Électronique (ID 1) ? ===")
    elec_prods = Product.query.filter_by(category_id=1).filter(Product.cj_pid.isnot(None)).all()
    suspects = []
    for p in elec_prods:
        nl = p.name.lower()
        if any(kw in nl for kw in ['lingerie', 'bra', 'underwear', 'dress', 'bikini', 'sexy']):
            suspects.append(p.name[:60])
    if suspects:
        print(f"  PROBLÈME: {len(suspects)} produits suspects !")
        for s in suspects:
            print(f"    {s}")
    else:
        print("  OK - Aucun produit mode dans Électronique")
    
    # Vérifier qu'aucun produit jardin n'est dans Sports
    print("\n=== Produits jardin dans Sports (ID 100) ? ===")
    sports_prods = Product.query.filter_by(category_id=100).filter(Product.cj_pid.isnot(None)).all()
    garden_suspects = []
    for p in sports_prods:
        nl = p.name.lower()
        if any(kw in nl for kw in ['garden', 'planter', 'greenhouse', 'flower stand', 'plant stand', 'gazebo', 'porch swing']):
            garden_suspects.append(p.name[:60])
    if garden_suspects:
        print(f"  PROBLÈME: {len(garden_suspects)} produits jardin dans Sports !")
        for s in garden_suspects:
            print(f"    {s}")
    else:
        print("  OK - Aucun produit jardin dans Sports")
    
    # Vérifier Mode & Vêtements - pas de produits tech
    print("\n=== Produits tech dans Mode (ID 52) ? ===")
    mode_prods = Product.query.filter_by(category_id=52).filter(Product.cj_pid.isnot(None)).all()
    tech_suspects = []
    for p in mode_prods:
        nl = p.name.lower()
        if any(kw in nl for kw in ['monitor', 'laptop', 'computer', 'phone case', 'bluetooth', 'camera', 'drone', 'sensor']):
            tech_suspects.append(p.name[:60])
    if tech_suspects:
        print(f"  PROBLÈME: {len(tech_suspects)} produits tech dans Mode !")
        for s in tech_suspects[:10]:
            print(f"    {s}")
    else:
        print("  OK - Aucun produit tech dans Mode")
