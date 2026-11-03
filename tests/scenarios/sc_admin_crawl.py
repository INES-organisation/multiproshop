import os, sys, re, json
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); sys.path.insert(0, ROOT); os.chdir(ROOT)
os.environ.pop('INES_API_KEY', None)
import app as appmod
from extensions import db, cache
app = appmod.create_app('testing')
from models.category import Category
from models.product import Product
from models.user import User
from models.role import Role
from models.order import Order
with app.app_context():
    db.drop_all(); db.create_all(); cache.clear()
    c = Category(name='Animalerie', slug='a', level=1, is_active=True, visible=True); db.session.add(c); db.session.flush()
    p = Product(name='Arbre', slug='arbre', sku='S1', price=39.9, cost_price=12.0, stock=50, category_id=c.id, is_active=True, cj_pid='P1'); db.session.add(p)
    r = Role(name='admin'); db.session.add(r); db.session.flush()
    u = User(username='boss', email='b@x.com', role_id=r.id); u.set_password('pw123456'); db.session.add(u)
    db.session.commit()
cl = app.test_client()
cl.post('/auth/admin-login', data={'username': 'boss', 'password': 'pw123456'})
res = {}
links = set()
for rule in app.url_map.iter_rules():
    if 'GET' not in rule.methods or rule.arguments or not (rule.rule.startswith('/admin')): continue
    try:
        resp = cl.get(rule.rule)
        code = resp.status_code
        body = resp.get_data(as_text=True) if 'html' in (resp.content_type or '') else ''
        for h in re.findall(r'href="([^"#][^"]*)"', body):
            if h.startswith('/'): links.add(h.split('?')[0])
        dead = len(re.findall(r'href="#"', body))
    except Exception as e:
        code, dead = 'EXC ' + type(e).__name__ + ': ' + str(e)[:80], 0
    res[rule.rule] = (code, rule.endpoint, dead)
for k, v in sorted(res.items()): print(v[0], k, v[1], 'href#=%d' % v[2])
bad = {}
for l in sorted(links):
    if l.startswith('/static'): continue
    try: code = cl.get(l).status_code
    except Exception as e: code = 'EXC'
    if code not in (200, 302): bad[l] = code
print('LIENS CASSES', json.dumps(bad, indent=0))
with app.app_context():
    u2 = User(username='autre', email='a@x.com'); u2.set_password('x'*8); db.session.add(u2); db.session.commit(); uid = u2.id
cl.post('/auth/admin-login', data={'username': 'boss', 'password': 'pw123456'})
print('delete autre', cl.get(f'/admin/users/delete/{uid}').status_code)
r = cl.get('/admin/products/export'); print('export', r.status_code, r.get_data(as_text=True)[:300])
