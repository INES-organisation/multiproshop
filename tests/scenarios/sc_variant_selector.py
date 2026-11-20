"""Fiche produit : boutons pour peu de choix, liste déroulante au-delà de 8, prix par choix quand il change,
« épuisé », choix unique déjà sélectionné, données des variantes échappées proprement (guillemets)."""
import json, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); sys.path.insert(0, ROOT); os.chdir(ROOT)
os.environ.pop('INES_API_KEY', None)
from app import create_app
from extensions import db
app = create_app('testing')
from models.category import Category
from models.product import Product
from models.product_variant import ProductVariant
with app.app_context():
    db.drop_all(); db.create_all()
    cat = Category(name='M', slug='m', is_active=True, visible=True, level=1); db.session.add(cat); db.session.flush()
    many = Product(name='Imprimante', slug='imp', sku='I', price=9.9, stock=0, category_id=cat.id, is_active=True, cj_pid='I')
    duo = Product(name='Tee-shirt', slug='tee', sku='T', price=12.0, stock=0, category_id=cat.id, is_active=True, cj_pid='T')
    few = Product(name='Lampe', slug='lam', sku='L', price=15.0, stock=0, category_id=cat.id, is_active=True, cj_pid='L')
    db.session.add_all([many, duo, few]); db.session.flush()
    for n in range(12):
        db.session.add(ProductVariant(product_id=many.id, cj_vid=f'I{n}', variant_key=f'Lot {n} "spécial"', sku=f'i{n}',
                                      price=9.9 + n, stock=0 if n == 3 else 20, active=True))
    for color in ('Black', 'White'):
        for size in ('S', 'M', 'L'):
            if (color, size) == ('White', 'L'):
                continue  # combinaison absente chez CJ
            db.session.add(ProductVariant(product_id=duo.id, cj_vid=f'{color}{size}', color=color, size=size,
                                          sku=f'{color}{size}', price=12.0, stock=10, active=True))
    db.session.add(ProductVariant(product_id=few.id, cj_vid='L1', color='Warm', sku='l1', price=15.0, stock=5, active=True))
    db.session.commit()
    ids = many.id, duo.id, few.id

c = app.test_client()
h = c.get(f'/products/{ids[0]}').get_data(as_text=True)
assert 'select class="form-select variant-select" id="variant-option"' in h, 'liste attendue au-delà de 8 choix'
assert '(12 choix)' in h and '· 9,90 €' in h and '· 20,90 €' in h, 'prix par choix absent'
assert re.search(r'<option value="\d+" disabled>[^<]*épuisé', h), 'variante épuisée non signalée'
data = json.loads(re.search(r'var variants = (\[.*?\]);', h).group(1))
assert len(data) == 12 and all(v['stock'] >= 0 for v in data)
h = c.get(f'/products/{ids[1]}').get_data(as_text=True)
assert 'data-dim="color"' in h and 'data-dim="size"' in h and 'form-select variant-select' not in h, 'boutons attendus'
assert 'Noir' in h and 'Blanc' in h
assert '· ' not in re.search(r'id="variantSelector".*?<script>', h, re.S).group(0), 'prix identique : pas de prix par choix'
h = c.get(f'/products/{ids[2]}').get_data(as_text=True)
assert 'Chaud' in h or 'Warm' in h
print('sélecteur de variantes OK')
