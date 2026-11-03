import os, sys
from datetime import datetime, timedelta
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); sys.path.insert(0, ROOT); os.chdir(ROOT)
import app as appmod
from extensions import db, cache
app = appmod.create_app('testing')
from models.category import Category
from models.product import Product
from services.product_service import ProductService
with app.app_context():
    db.drop_all(); db.create_all()
    full = Category(name='Animalerie', slug='animalerie', level=1, is_active=True, visible=True)
    empty = Category(name='Immobilier', slug='immobilier', level=1, is_active=True, visible=True)
    db.session.add_all([full, empty]); db.session.flush()
    sub = Category(name='Jouets chat', slug='jouets-chat', level=2, parent_id=full.id, is_active=True, visible=True)
    sub_empty = Category(name='Aquariums', slug='aquariums', level=2, parent_id=full.id, is_active=True, visible=True)
    db.session.add_all([sub, sub_empty]); db.session.flush()
    def prod(i, name, price, curated, active=True, cat=sub):
        p = Product(name=name, slug=f'p{i}', sku=f'S{i}', price=price, stock=50, category_id=cat.id, is_active=active,
                    published_at=datetime.utcnow() - timedelta(days=i) if curated else None)
        db.session.add(p); return p
    for i in range(10):
        prod(i, f'Raw Product {i}', 0.9 + i, False)
    prod(20, 'Arbre à chat', 39.9, True); prod(21, 'Fontaine à eau', 24.9, True); prod(22, 'Ancien retiré', 19.9, False, active=False)
    db.session.commit(); cache.clear()
    c = app.test_client()
    h = c.get('/').get_data(as_text=True)
    assert 'Arbre à chat' in h and 'Fontaine à eau' in h, 'accueil'
    import re; print([l.strip() for l in h.splitlines() if re.search('Immobilier|Aquariums|Jouets chat', l)][:8])
    assert 'Immobilier' not in h and 'Aquariums' not in h and 'Jouets chat' in h, 'menu'
    print('accueil et menu ok')
    h = c.get('/products/').get_data(as_text=True)
    assert h.index('Arbre à chat') < h.index('Raw Product') and 'Notre sélection' in h, 'liste'
    h = c.get(f'/products/cat/{full.id}', follow_redirects=True).get_data(as_text=True)
    assert 'Ancien retiré' not in h and h.index('Arbre à chat') < h.index('Raw Product'), 'catégorie'
    print('liste et catégorie ok')
    r = c.get('/recherche?q=a') if False else None
    feat = ProductService.get_featured_products()
    assert {p.name for p in feat} == {'Arbre à chat', 'Fontaine à eau'}, feat
    print('TOUT OK menu')
