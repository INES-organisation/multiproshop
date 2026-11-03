import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); sys.path.insert(0, ROOT); os.chdir(ROOT)
os.environ.pop('INES_API_KEY', None)
import app as appmod
from extensions import db, cache
app = appmod.create_app('testing'); appmod.app = app
from models.category import Category
from models.coupon import Coupon
from models.newsletter import NewsletterSubscriber
from models.user import User
from models.role import Role
import utils.email as ue
sent = []
ue.send_email = lambda **kw: sent.append(kw)
with app.app_context():
    db.drop_all(); db.create_all(); cache.clear()
    c = Category(name='Maison', slug='m', level=1, is_active=True, visible=True); db.session.add(c)
    ra = Role(name='admin'); db.session.add(ra); db.session.flush()
    a = User(username='boss', email='b@x.com', role_id=ra.id); a.set_password('pw123456'); db.session.add(a)
    db.session.add(Coupon(code='DIX', kind='percent', value=10))
    db.session.commit(); cid, aid = c.id, a.id
cl = app.test_client()
page = cl.get('/').get_data(as_text=True); assert 'newsletter' in page.lower() and '-10' in page
r = cl.post('/newsletter', json={'email': 'a@b.fr'}); assert r.status_code == 400 and 'Cochez' in r.json['message']
r = cl.post('/newsletter', json={'email': 'pas-un-mail', 'consent': True}); assert r.status_code == 400
r = cl.post('/newsletter', json={'email': 'bot@b.fr', 'consent': True, 'website': 'x'}); assert r.json['ok']
r = cl.post('/newsletter', json={'email': ' Ana@B.fr ', 'consent': True}); assert r.json['ok'] and r.json['code'].startswith('BIENVENUE-'), r.json
code = r.json['code']
assert len(sent) == 1 and sent[0]['to'] == 'ana@b.fr' and code in sent[0]['html'] and '/newsletter/desinscription/' in sent[0]['html']
with app.app_context():
    assert NewsletterSubscriber.query.count() == 1
    cp = Coupon.query.filter_by(code=code).first(); assert cp.value == 10 and cp.max_uses == 1 and cp.min_subtotal == 20 and cp.ends_at
    tok = NewsletterSubscriber.query.first().token
r = cl.post('/newsletter', data={'email': 'ana@b.fr', 'consent': 'on'}); assert r.json['ok'] and r.json['code'] == code and 'déjà' in r.json['message']
with app.app_context(): assert Coupon.query.filter(Coupon.note.like('newsletter %')).count() == 1
print('inscription, code personnel, renvoi OK')
r = cl.get(f'/newsletter/desinscription/{tok}'); assert r.status_code == 302
with app.app_context(): assert NewsletterSubscriber.query.first().unsubscribed_at
print('désinscription OK')
cl.post('/newsletter', json={'email': 'zoe@b.fr', 'consent': True})
adm = app.test_client()
with adm.session_transaction() as s: s['_user_id'] = str(aid); s['_fresh'] = True
html = adm.get('/admin/coupons').get_data(as_text=True)
assert 'DIX' in html and 'BIENVENUE-' not in html and '1 inscrit' in html, html[html.find('Newsletter'):][:300]
csv = adm.get('/admin/newsletter.csv'); assert csv.status_code == 200 and 'zoe@b.fr' in csv.get_data(as_text=True) and 'ana@b.fr' not in csv.get_data(as_text=True)
assert cl.get('/admin/newsletter.csv').status_code in (302, 401, 403)
print('admin résumé + CSV OK')
r = cl.get(f'/products/cat/{cid}?sort=price'); assert r.status_code == 301 and f'/category/{cid}' in r.location and 'sort=price' in r.location, (r.status_code, r.location)
print('/cat 301 OK')
