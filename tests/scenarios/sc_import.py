import os, sys, json
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); sys.path.insert(0, ROOT); os.chdir(ROOT)
os.environ.pop('INES_API_KEY', None)
import app as appmod
from extensions import db
appmod.app = app = appmod.create_app('testing')
from models.category import Category
from models.product import Product
from models.product_variant import ProductVariant
with app.app_context():
    db.create_all()
    db.session.add(Category(name='Pet Toys', slug='pet-toys', is_active=True, visible=True, level=2)); db.session.commit()
import scripts.import_selection as imp
imp.app = app
raw = {'pid': 'P1', 'productNameEn': 'Cat Toy', 'productSku': 'SKU-P1', 'sellPrice': '3.0-5.0', 'description': '<p>d</p>',
       'productImage': '["a.jpg","b.jpg"]', 'productWeight': '200', 'categoryId': 'unknown',
       'variants': [{'vid': 'V1', 'variantKey': 'Red-S', 'variantSellPrice': '3.0'}, {'vid': 'V2', 'variantKey': 'Blue', 'variantSellPrice': '5.0'}]}
class FakeApi(imp.CJDropshippingApiOptimized):
    def __init__(self, **k): pass
    def _make_request(self, m, ep, params=None, **k): return {'result': True, 'data': raw}
imp.CJDropshippingApiOptimized = FakeApi
item = {'pid': 'P1', 'nom_en': 'Cat Toy', 'nom_fr': 'Jouet pour chat', 'famille': 'Animaux', 'categorie_cj': 'Pet Supplies > Pet Toys',
        'cout_eur': 4.6, 'prix_vente_eur': 11.9, 'stock': 500, 'image': 'a.jpg'}
import tempfile; path = os.path.join(tempfile.mkdtemp(), 'sel_test.json')
json.dump([item, item], open(path, 'w'))
for argv in ([path, '--dry-run'], [path], [path]):
    sys.argv = ['x'] + argv; imp.main()
with app.app_context():
    p = Product.query.filter_by(cj_pid='P1').one()
    vs = ProductVariant.query.filter_by(product_id=p.id).order_by(ProductVariant.cj_vid).all()
    print('has_range', p.has_price_range); print(p.name, p.price, p.compare_price, p.stock, p.category.name, p.is_active, p.published, [(v.cj_vid, v.price, v.color, v.size) for v in vs])
    c = app.test_client()
    r = c.get(f'/products/{p.id}'); print('fiche', r.status_code)
    r = c.post('/cart/add', json={'product_id': p.id, 'quantity': 1, 'variant_id': vs[1].id}); print('panier', r.status_code, r.json.get('message'))
sys.argv = ['x', path, '--unpublish']; imp.main()
with app.app_context():
    p = Product.query.filter_by(cj_pid='P1').one(); p.is_active = True; db.session.commit()
    h = app.test_client().get('/products/').get_data(as_text=True)
    print('liste à partir de', 'à partir de' in h)
    h = app.test_client().get(f'/products/{p.id}').get_data(as_text=True)
    print('fiche à partir de', 'id="price-from"' in h)
