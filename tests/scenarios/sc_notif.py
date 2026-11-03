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
from models.order import Order
from models.user import User
from models.role import Role
from models.admin_notification import AdminNotification
with app.app_context():
    db.drop_all(); db.create_all(); cache.clear()
    c = Category(name='Maison', slug='m', level=1, is_active=True, visible=True); db.session.add(c); db.session.flush()
    p = Product(name='Lampe', slug='l', sku='L', price=10, cost_price=5, stock=4, category_id=c.id, is_active=True, published_at=datetime.utcnow(), cj_pid='P1')
    db.session.add(p); db.session.flush()
    db.session.add(ProductVariant(product_id=p.id, cj_vid='V1', variant_key='x', price=10, stock=4, active=True, cj_raw_data=json.dumps({'price': 12.0})))
    o = Order(order_number='ORD-1', status='paid', payment_status='paid', subtotal=10, shipping_cost=0, total_price=10, customer_email='a@b.fr',
              shipping_first_name='A', shipping_last_name='B', shipping_address='x', shipping_city='y', shipping_postal_code='1', cj_order_id='CJ123')
    db.session.add(o)
    ra = Role(name='admin'); db.session.add(ra); db.session.flush()
    a = User(username='boss', email='b@x.com', role_id=ra.id); a.set_password('pw123456'); db.session.add(a)
    db.session.commit(); aid, pid, oid = a.id, p.id, o.id
    from services.notifications import check_margin, notify, unread_count
    check_margin(Product.query.get(pid)); check_margin(Product.query.get(pid))
    assert AdminNotification.query.filter_by(kind='margin').count() == 1
    from services import cj_disputes
    class Api:
        def get_disputes(self, page=1, size=20, order_id=None):
            return {'list': [{'id': 'D1', 'orderId': 'CJ123', 'disputeReason': 'Colis perdu', 'status': 'PROCESSING', 'money': 9.5}], 'total': 1} if page == 1 else {'list': [], 'total': 1}
    assert cj_disputes.check_new(Api()) == 1 and cj_disputes.check_new(Api()) == 0
    assert unread_count() == 2
import routes.admin as adm
adm._cj_api = lambda: Api()
cl = app.test_client()
with cl.session_transaction() as s: s['_user_id'] = str(aid); s['_fresh'] = True
h = cl.get('/admin/').get_data(as_text=True); assert 'admin-notification-badge">2<' in h, 'badge'
h = cl.get('/admin/notifications').get_data(as_text=True); assert 'Marge négative' in h and 'Litige CJ D1' in h
cl.post('/admin/notifications')
with app.app_context(): assert AdminNotification.query.filter_by(read_at=None).count() == 0
h = cl.get('/admin/litiges').get_data(as_text=True); assert 'Colis perdu' in h and '#ORD-1' in h, h[-2000:]
h = cl.get(f'/admin/orders/{oid}').get_data(as_text=True); assert 'Litiges de cette commande' in h
r = cl.get('/admin/products?search=lamp'); assert r.status_code == 200
print('notifications (marge, litiges), cloche, page litiges, fiche commande OK')
