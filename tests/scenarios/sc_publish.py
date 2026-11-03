import os, sys, json
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); sys.path.insert(0, ROOT); os.chdir(ROOT)
os.environ.pop('INES_API_KEY', None)
import app as appmod
from extensions import db, cache
from datetime import datetime
app = appmod.create_app('testing'); appmod.app = app
from models.category import Category
from models.product import Product
from models.product_variant import ProductVariant
from models.user import User
from models.role import Role
import services.publication as pub
assert [pub.grid_price(c) for c in (1.0, 4.6, 9.99, 10, 14.95, 30, 52.3)] == [9.9, 11.9, 25.9, 25.9, 29.9, 60.9, 83.9], [pub.grid_price(c) for c in (1.0, 4.6, 9.99, 10, 14.95, 30, 52.3)]
stock = {'V1': 5, 'V2': 0}
answer = {'on': True}
class Api:
    def get_variant_inventory(self, vid):
        return [{'country': 'CN', 'total': stock.get(vid, 0)}] if answer['on'] else None
class Ship:
    def refresh_product_rate(self, product, country): return [{'name': 'CJPacket', 'price': 5.0}]
pub._api = lambda: Api(); pub._shipping = lambda: Ship()
with app.app_context():
    db.drop_all(); db.create_all(); cache.clear()
    c = Category(name='Maison', slug='m', level=1, is_active=True, visible=True); db.session.add(c); db.session.flush()
    p = Product(name='Lampe', slug='l', sku='L', price=3, cost_price=4, stock=999, category_id=c.id, is_active=False, cj_pid='PL')
    q = Product(name='Vase', slug='v', sku='V', price=50, cost_price=4, stock=999, category_id=c.id, is_active=False, cj_pid='PV')
    db.session.add_all([p, q]); db.session.flush()
    db.session.add_all([ProductVariant(product_id=p.id, cj_vid='V1', sku='a', price=3, stock=999, active=True, cj_raw_data=json.dumps({'price': 5.0})),
                        ProductVariant(product_id=p.id, cj_vid='V2', sku='b', price=3, stock=999, active=True, cj_raw_data=json.dumps({'price': 20.0})),
                        ProductVariant(product_id=q.id, cj_vid='V2', sku='c', price=50, stock=999, active=True) if False else
                        ProductVariant(product_id=q.id, cj_vid='Q1', sku='c', price=50, stock=999, active=True)])
    ra = Role(name='admin'); db.session.add(ra); db.session.flush()
    a = User(username='boss', email='b@x.com', role_id=ra.id); a.set_password('pw123456'); db.session.add(a)
    db.session.commit(); pid, qid, aid = p.id, q.id, a.id
cl = app.test_client()
with cl.session_transaction() as s: s['_user_id'] = str(aid); s['_fresh'] = True
# CJ muet : refus, rien n'est publié
answer['on'] = False
r = cl.post(f'/admin/api/cj/product/{pid}/publish', json={'active': True}); assert r.status_code == 400 and 'répondu' in r.json['message'], r.json
answer['on'] = True
# Stock relu, grille appliquée par variante, prix affiché = la moins chère
r = cl.post(f'/admin/api/cj/product/{pid}/publish', json={'active': True}); assert r.json['success'], r.json
with app.app_context():
    p = Product.query.get(pid); v1, v2 = ProductVariant.query.filter_by(product_id=pid).order_by(ProductVariant.id).all()
    assert p.is_active and p.stock == 5 and v1.stock == 5 and v2.stock == 0, (p.stock, v1.stock, v2.stock)
    assert v1.price == 11.9 and v2.price == 36.9 and p.price == 11.9, (v1.price, v2.price, p.price)
    v1.price = 15.0; p.price = 15.0; db.session.commit()
# Retirer puis republier : le prix fixé à la main est gardé
cl.post(f'/admin/api/cj/product/{pid}/publish', json={'active': False})
r = cl.post(f'/admin/api/cj/product/{pid}/publish', json={'active': True}); assert r.json['success']
with app.app_context(): assert ProductVariant.query.filter_by(cj_vid='V1').first().price == 15.0
# Rupture chez CJ : refus, mais le stock relu est enregistré
r = cl.post(f'/admin/api/cj/product/{qid}/publish', json={'active': True}); assert r.status_code == 400 and 'rupture' in r.json['message'], r.json
with app.app_context(): assert Product.query.get(qid).stock == 0
# Fiche produit : publier avec un prix saisi à la main le garde
stock['Q1'] = 7
with app.app_context(): q = Product.query.get(qid); form = {'name': q.name, 'sku': q.sku, 'price': '19.90', 'stock': '0', 'category_id': str(q.category_id), 'is_active': 'on'}
r = cl.post(f'/admin/products/edit/{qid}', data=form)
with app.app_context():
    q = Product.query.get(qid); assert q.is_active and q.price == 19.9 and q.stock == 7 and q.published_at, (q.is_active, q.price, q.stock)
print('publication : stock CJ, grille, refus, prix manuel OK')

# --- Enrichissement CJ, variantes réparées, rédaction par Claude via INES (tâche de fond simulée) ---
import services.ai_copy as ai
from utils.variant_keys import split_variant_key
with app.app_context():
    r = Product(name='Mens Retro Loose-fit Casual Athletic Pants', slug='pants', sku='PANTS', price=5, cost_price=8, stock=0,
                category_id=Category.query.first().id, is_active=False, cj_pid='PANTS')
    db.session.add(r); db.session.flush()
    db.session.add(ProductVariant(product_id=r.id, cj_vid='P1', variant_key='Khaki-4XL', color='Mens Retro Loose',
                                  size='fit Casual Athletic Pants Khaki 4XL', sku='p1', stock=0, active=True))
    db.session.commit(); rid = r.id
stock['P1'] = 30; stock['P2'] = 12
def details(self, pid):
    return {'pid': pid, 'description': '<p>Product information: Color: Black, Khaki</p>', 'images': ['http://x/1.jpg', 'http://x/2.jpg'],
            'weight': '500', 'material': 'Polyester', 'raw_data': {'productKeyEn': 'Color-Size'},
            'variants': [{'vid': 'P1', 'key': 'Khaki-4XL', 'price': 8.0, 'sku': 'p1'},
                         {'vid': 'P2', 'key': 'Black-M', 'price': 8.0, 'sku': 'p2'}]}
Api.get_product_details = details
os.environ['INES_API_KEY'] = 'test-key'
ai._generate = lambda system, prompt, max_tokens=3000: json.dumps({
    'name': 'Pantalon cargo homme coupe ample', 'intro': 'Un pantalon de travail confortable.',
    'bullets': ['Coupe ample', 'Tissu légèrement extensible', 'Poches cargo'],
    'details_html': '<p>Texte</p><script>alert(1)</script><h3>Caractéristiques</h3><ul><li onclick="x">Polyester</li></ul>',
    'specs': {'Matière': 'Polyester'}, 'meta_title': 'Pantalon cargo homme', 'meta_description': 'Pantalon cargo ample.',
    'options': {'Khaki': 'Kaki', 'Black': 'Noir'}})
queued = []
pub._queue = lambda product_id: queued.append(product_id)
r = cl.post(f'/admin/api/cj/product/{rid}/publish', json={'active': True}); assert r.json['success'] and r.json['queued'], r.json
with app.app_context():
    r = Product.query.get(rid)
    assert not r.is_active and r.weight == 500 and len(r.get_images_list()) == 2 and 'Product information' in r.description
    v1 = ProductVariant.query.filter_by(cj_vid='P1').first(); v2 = ProductVariant.query.filter_by(cj_vid='P2').first()
    assert (v1.color, v1.size) == ('Khaki', '4XL'), (v1.color, v1.size)
    assert v2 is not None and not v2.active and (v2.color, v2.size) == ('Black', 'M'), 'nouvelle variante CJ inactive'
    assert queued == [rid]
    res = pub.write_and_publish(rid)
    r = Product.query.get(rid); v1 = ProductVariant.query.filter_by(cj_vid='P1').first()
    assert res == {'published': rid} and r.is_active and r.published_at and r.name == 'Pantalon cargo homme coupe ample', (res, r.name)
    assert '<script>' not in r.description and 'onclick' not in r.description and '<h3>Caractéristiques</h3>' in r.description
    assert r.short_description.count('\n') == 2 and r.get_specifications() == {'Matière': 'Polyester'} and v1.color == 'Kaki'
    assert r.price == 18.9, r.price  # coût 8 $ = 7,36 € x 2,5 = 18,40 -> 18,90
print('publication : enrichissement CJ, variantes réparées, rédaction Claude puis mise en ligne OK')
