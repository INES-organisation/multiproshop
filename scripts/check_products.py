import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models.product import Product

with app.app_context():
    print("\n" + "="*80)
    print("VERIFICATION DES PRODUITS")
    print("="*80 + "\n")
    
    total = Product.query.count()
    actifs = Product.query.filter_by(is_active=True).count()
    inactifs = Product.query.filter_by(is_active=False).count()
    
    print(f"Total produits: {total}")
    print(f"Produits actifs (is_active=True): {actifs}")
    print(f"Produits inactifs (is_active=False): {inactifs}")
    
    print("\n" + "-"*80)
    print("Premiers 10 produits:")
    print("-"*80 + "\n")
    
    products = Product.query.limit(10).all()
    for p in products:
        print(f"ID: {p.id:3} | Actif: {p.is_active} | Nom: {p.name[:50]}")
    
    print("\n" + "="*80 + "\n")
