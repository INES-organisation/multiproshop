import os, sys
from datetime import datetime, timedelta
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); sys.path.insert(0, ROOT); os.chdir(ROOT)
os.environ.pop('INES_API_KEY', None)
from app import create_app
from extensions import db
app = create_app('testing')
from models.category import Category
from models.product import Product
from models.order import Order, OrderItem
from models.review_request import ReviewRequest
import utils.email as ue
sent = []
ue._send_via_ines = lambda to, subject, html: sent.append((to, subject, html)) or True
with app.app_context():
    db.create_all()
    cat = Category(name='M', slug='m', is_active=True, visible=True, level=1); db.session.add(cat); db.session.flush()
    p = Product(name='Lampe LED', slug='lampe', sku='S1', price=20.0, stock=5, category_id=cat.id, is_active=True, cj_pid='P1')
    q = Product(name='Tapis', slug='tapis', sku='S2', price=10.0, stock=5, category_id=cat.id, is_active=True, cj_pid='P2')
    db.session.add_all([p, q]); db.session.flush()
    def order(**kw):
        o = Order(customer_email='a@b.fr', shipping_first_name='anne', shipping_last_name='dupont', shipping_address='1', shipping_city='L',
                  shipping_postal_code='1', status='delivered', payment_status='paid', total_price=30, subtotal=30, **kw)
        db.session.add(o); db.session.flush()
        db.session.add_all([OrderItem(order_id=o.id, product_id=p.id, quantity=1, price=20), OrderItem(order_id=o.id, product_id=q.id, quantity=1, price=10)])
        return o
    now = datetime.utcnow()
    o1 = order(delivered_at=now - timedelta(days=8))
    order(delivered_at=now - timedelta(days=2))                       # trop tôt
    order(shipped_at=now - timedelta(days=22))                        # jamais confirmé livré
    order(delivered_at=now - timedelta(days=8), created_at=now - timedelta(days=120))  # trop ancien
    db.session.commit()
    from services import review_requests
    print('envoyés', review_requests.send_due(), review_requests.send_due())
    assert len(sent) == 2 and 'Lampe LED' in sent[0][2]
    token = ReviewRequest.query.filter_by(order_id=o1.id).one().token
    pid, qid = p.id, q.id
c = app.test_client()
r = c.get(f'/avis/{token}'); assert r.status_code == 200 and 'Tapis' in r.get_data(as_text=True)
r = c.post(f'/avis/{token}', data={f'rating_{pid}': '4', f'comment_{pid}': 'Très bien'}); assert r.status_code == 302
h = c.get(f'/avis/{token}').get_data(as_text=True); assert 'Tapis' in h and 'Lampe LED' not in h
r = c.post(f'/avis/{token}', data={f'rating_{qid}': '2'}); 
h = c.get(f'/avis/{token}').get_data(as_text=True); assert "plus d'article" in h
h = c.get(f'/products/{pid}').get_data(as_text=True); assert 'Anne D.' in h and 'Très bien' in h, 'avis absent de la fiche'
assert c.get('/avis/xxx').status_code == 404
print('avis ok')
