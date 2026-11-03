import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); sys.path.insert(0, ROOT); os.chdir(ROOT)
os.environ.pop('INES_API_KEY', None)
from datetime import datetime, timedelta
import app as appmod
from extensions import db, cache
app = appmod.create_app('testing')
appmod.app = app
from models.category import Category
from models.product import Product
from models.product_variant import ProductVariant
from models.shipping_rate import ShippingRate
import services.shipping_service as ss
calls = []
class FakeApi:
    def calculate_shipping(self, products, country, start_country='CN'):
        calls.append((country, products[0]['vid']))
        if products[0]['vid'] == 'VDOWN': return None
        if country == 'FR':
            return [{'logisticName': 'CJPacket', 'logisticPrice': 5.0, 'logisticAging': '14-18'},
                    {'logisticName': 'DHL', 'logisticPrice': 40.0, 'logisticAging': '5-8'}]
        return []
    def get_variant_inventory(self, vid): return [{'country': 'CN', 'total': 5}]
ss.ShippingService.__init__ = lambda self: setattr(self, 'cj_api', FakeApi())
with app.app_context():
    db.drop_all(); db.create_all(); cache.clear()
    c = Category(name='Maison', slug='m', level=1, is_active=True, visible=True); db.session.add(c); db.session.flush()
    now = datetime.utcnow()
    a = Product(name='Lampe', slug='lampe', sku='S1', price=60.0, cost_price=20.0, stock=50, category_id=c.id, is_active=True, cj_pid='P1', published_at=now)
    b = Product(name='Brouillon', slug='b', sku='S2', price=60.0, cost_price=20.0, stock=50, category_id=c.id, is_active=False, cj_pid='P2')
    d = Product(name='Panne', slug='d', sku='S3', price=60.0, cost_price=20.0, stock=50, category_id=c.id, is_active=True, cj_pid='P3', published_at=now)
    db.session.add_all([a, b, d]); db.session.flush()
    for p, vid in ((a, 'V1'), (b, 'V2'), (d, 'VDOWN')):
        db.session.add(ProductVariant(product_id=p.id, cj_vid=vid, variant_key='x', price=60, stock=10, active=True))
    # ancien tarif freightCalculateTip : ne doit pas être lu par la fiche
    ShippingRate.upsert(a.id, 'FR', [{'name': 'OLD', 'price': 99, 'delivery_time': '1-2'}], source='cj')
    db.session.commit(); aid, bid, did = a.id, b.id, d.id

    from tasks.shipping_rate_tasks import refresh_shipping_rates
    r = refresh_shipping_rates.run()
    print(r)
    assert r['success'] and r['updated'] == 1 and r['not_deliverable'] == 1 and r['skipped'] == 2, r
    fr = ShippingRate.get_for_product(aid, 'FR'); re_ = ShippingRate.get_for_product(aid, 'RE')
    assert fr.source == 'freight' and fr.methods[0]['name'] == 'CJPacket', fr.methods
    assert re_.source == 'freight_empty' and re_.methods == []
    assert ShippingRate.get_for_product(bid, 'FR') is None  # brouillon ignoré
    # second passage : tarifs frais non redemandés
    n = len(calls); r2 = refresh_shipping_rates.run()
    assert r2['fresh'] == 2 and len([x for x in calls[n:] if x[1] == 'V1']) == 0, (r2, calls[n:])
    print('tâche hebdomadaire OK')

    # fiche produit : lit la base sans appeler CJ
    cache.clear(); n = len(calls)
    svc = ss.ShippingService()
    e = svc.product_estimate(Product.query.get(aid), 'FR')
    assert e['available'] and e['cheapest']['name'] == 'CJPacket' and e['fastest']['name'] == 'DHL', e
    assert svc.product_estimate(Product.query.get(aid), 'RE') == {'available': False}
    assert len(calls) == n, calls[n:]
    # tarif expiré : appel CJ en direct puis enregistrement
    fr = ShippingRate.get_for_product(aid, 'FR'); fr.synced_at = now - timedelta(days=9); db.session.commit()
    e = svc.product_estimate(Product.query.get(aid), 'FR')
    assert e['available'] and len(calls) == n + 1
    assert not ShippingRate.get_for_product(aid, 'FR').is_expired(1)
    # CJ injoignable : rien enregistré
    assert svc.product_estimate(Product.query.get(did), 'FR') is None
    assert ShippingRate.get_for_product(did, 'FR') is None
    print('fiche produit depuis la base OK')
    # la page de la fiche
    cl = app.test_client()
    resp = cl.get(f'/products/{aid}/livraison?country=FR')
    print(resp.status_code, resp.get_data(as_text=True)[:200])
