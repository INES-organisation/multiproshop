import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); sys.path.insert(0, ROOT); os.chdir(ROOT)
import app as appmod
from extensions import db, cache
app = appmod.create_app('testing'); appmod.app = app
from models.admin_notification import AdminNotification
@app.route('/cart/boom')
def boom():
    raise ValueError('panne simulée')
with app.app_context():
    db.drop_all(); db.create_all(); cache.clear()
app.testing = False  # l'alerte est coupée en mode test ; on simule la production
app.config['PROPAGATE_EXCEPTIONS'] = False
cl = app.test_client()
for _ in range(3):
    assert cl.get('/cart/boom').status_code == 500
with app.app_context():
    ns = AdminNotification.query.filter_by(kind='error').all()
    assert len(ns) == 1 and ns[0].level == 'danger' and 'panne simulée' in ns[0].message and '/cart/boom' in ns[0].title, [(n.title, n.message) for n in ns]
print('erreur 500 → une notification admin (sans doublon) OK')
