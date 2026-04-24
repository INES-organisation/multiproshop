import sys
import os
sys.path.insert(0, r'c:\Users\Anthony\CascadeProjects\multiproshop')

from app import create_app
from models.product import Product

app = create_app()

with app.app_context():
    prods = Product.query.limit(30).all()
    print('\n=== VERIFICATION CATEGORIES SUR /products/ ===\n')
    print(f'{"Produit":<50} | {"Categorie":<30} | CJ')
    print('-' * 90)
    for p in prods:
        cat = p.category.name[:30] if p.category else 'AUCUNE'
        cj = 'Oui' if p.cj_pid else 'Non'
        print(f'{p.name[:50]:<50} | {cat:<30} | {cj}')
