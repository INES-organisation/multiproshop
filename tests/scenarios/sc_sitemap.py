import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); sys.path.insert(0, ROOT); os.chdir(ROOT)
import app as appmod
from extensions import db
app = appmod.create_app('testing'); appmod.app = app
from models.category import Category
from models.product import Product

with app.app_context():
    db.drop_all(); db.create_all()
    parent = Category(name='Maison', slug='maison'); empty = Category(name='Vide', slug='vide')
    db.session.add_all([parent, empty]); db.session.flush()
    child = Category(name='Déco', slug='deco', parent_id=parent.id); db.session.add(child); db.session.flush()
    db.session.add(Product(name='P', slug='p', price=10, stock=1, category_id=child.id, is_active=True))
    db.session.add(Product(name='Q', slug='q', price=10, stock=1, category_id=empty.id, is_active=False))
    db.session.commit()
    ids = (parent.id, child.id, empty.id)
xml = app.test_client().get('/sitemap.xml').get_data(as_text=True)
assert f'/products/category/{ids[0]}<' in xml and f'/products/category/{ids[1]}<' in xml, xml  # parent via sa sous-catégorie
assert f'/products/category/{ids[2]}<' not in xml, xml  # aucun produit en ligne
print('sitemap sans catégories vides OK')
