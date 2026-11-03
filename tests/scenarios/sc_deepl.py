import os, sys, json
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); sys.path.insert(0, ROOT); os.chdir(ROOT)
os.environ['INES_API_KEY'] = 'test-key'
import app as appmod
from extensions import db, cache
app = appmod.create_app('testing'); appmod.app = app
from models.category import Category
from models.product import Product
from models.product_variant import ProductVariant
import services.translate as tr
import services.ai_copy as ai
import services.publication as pub
calls, prompts = [], []
mode = {'v': 'on'}
def fake_call(texts, target, source, context, html):
    calls.append(list(texts))
    if mode['v'] == 'off':
        return 'off'
    return [{'Coffee cup set': 'Lot de tasses à café', 'Starry sky projector': 'Projecteur ciel étoilé'}.get(t, t + ' FR') for t in texts]
tr._call = fake_call
def gen(system, prompt, max_tokens=3000):
    prompts.append(prompt)
    return json.dumps({'name': 'Projecteur ciel étoilé', 'intro': 'x', 'bullets': ['a'], 'details_html': '<p>t</p>',
                       'options': {'Starry sky projector': 'Mauvais'}})
ai._generate = gen
with app.app_context():
    db.drop_all(); db.create_all(); cache.clear()
    c = Category(name='Maison', slug='m', level=1, is_active=True, visible=True); db.session.add(c); db.session.flush()
    p = Product(name='Starry projector lamp for kids', slug='p', sku='S1', price=30.0, stock=5, category_id=c.id, is_active=False, cj_pid='P1')
    db.session.add(p); db.session.flush()
    for i, (col, size) in enumerate([('Starry sky projector', 'US Plug'), ('Coffee cup set', 'XL'), ('Wine Red', 'M')]):
        db.session.add(ProductVariant(product_id=p.id, cj_vid=f'V{i}', color=col, size=size, price=30, stock=5, active=True))
    db.session.commit(); pid = p.id
    # 1. DeepL traduit seulement les libellés que le traducteur local ne sait pas faire
    res = pub.write_and_publish(pid)
    assert res == {'published': pid}, res
    assert calls == [['Starry sky projector', 'Coffee cup set']], calls
    cols = sorted(v.color for v in ProductVariant.query.filter_by(product_id=pid))
    assert cols == ['Lot de tasses à café', 'Projecteur ciel étoilé', 'Wine Red'], cols
    assert 'Options proposées : aucune' in prompts[-1], 'Claude ne reçoit plus les options'
    print('DeepL pour les options, Claude pour la fiche OK')
    # 2. cache : le même libellé n'est pas retraduit
    assert tr.translate(['Coffee cup set']) == ['Lot de tasses à café'] and len(calls) == 1
    print('cache OK')
    # 3. DeepL absent d'INES : Claude reçoit les options
    cache.clear(); mode['v'] = 'off'
    v = ProductVariant.query.filter_by(cj_vid='V0').first(); v.color = 'Starry sky projector'
    p = Product.query.get(pid); p.published_at = None; db.session.commit()
    pub.write_and_publish(pid)
    assert 'Starry sky projector' in prompts[-1] and ProductVariant.query.filter_by(cj_vid='V0').first().color == 'Mauvais'
    assert tr.translate(['x']) is None and len(calls) == 2, 'pause de 10 min après un refus'
    print('repli sur Claude sans DeepL OK')
