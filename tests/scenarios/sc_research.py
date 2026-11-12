"""Recherche de produits : veille CJ par critères comparée au web (DataForSEO simulé), verdicts, import en
brouillon dans la vitrine, sourcing CJ, écart conservé au passage suivant, Claude qui complète les
recherches, reprise de la fiche d'une vitrine, et lecture des réponses DataForSEO."""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); sys.path.insert(0, ROOT); os.chdir(ROOT)
os.environ.pop('INES_API_KEY', None)
for k in ('DATAFORSEO_LOGIN', 'DATAFORSEO_PASSWORD', 'MULTIPROSHOP_DATAFORSEO_LOGIN', 'MULTIPROSHOP_DATAFORSEO_PASSWORD'):
    os.environ.pop(k, None)
import app as appmod
from extensions import db, cache
app = appmod.create_app('testing')
from models.category import Category
from models.cj_sourcing import CjSourcing
from models.product import Product
from models.product_research import ResearchResult, ResearchWatch
from models.role import Role
from models.user import User
from services.api_providers.cj_dropshipping_optimized import CJDropshippingApiOptimized as Api
import services.dataforseo as dfs
import services.product_research as research

# --- DataForSEO : Trends (moyenne sur 12 mois), tâche Amazon relue jusqu'à ce qu'elle soit prête ---
class Resp:
    def __init__(self, body, code=200): self.body, self.status_code = body, code
    def json(self): return self.body
sent = []
def fake_request(method, url, json=None, auth=None, timeout=None):
    sent.append((method, url.replace(dfs.API, ''), json))
    path = url.replace(dfs.API, '')
    if 'google_trends' in path:
        return Resp({'status_code': 20000, 'tasks': [{'cost': 0.011, 'result': [{'items': [{'type': 'google_trends_graph', 'data': [
            {'values': [40, 10]}, {'values': [60, None]}, {'values': [0, 0], 'missing_data': True}]}]}]}]})
    if path.endswith('task_post'):
        return Resp({'status_code': 20000, 'tasks': [{'id': 'T1', 'status_code': 20100, 'cost': 0.003}]})
    n = sum(1 for s in sent if 'task_get' in s[1])
    if n == 1:
        return Resp({'status_code': 20000, 'tasks': [{'id': 'T1', 'status_code': 40602, 'status_message': 'Task In Queue'}]})
    return Resp({'status_code': 20000, 'tasks': [{'id': 'T1', 'status_code': 20000, 'result': [{'items': [
        {'data_asin': 'B01', 'title': 'Micro cravate', 'price_from': 19.99, 'currency': 'EUR', 'bought_past_month': 2000,
         'rating': {'value': 4.4, 'votes_count': 812}, 'image_url': 'https://m/1.jpg', 'url': 'https://amazon.fr/dp/B01'},
        {'data_asin': 'B02', 'title': 'Micro en dollars', 'price_from': 9, 'currency': 'USD'},
        {'title': 'sans ASIN'}]}]}]})
dfs.requests.request = fake_request
assert not dfs.configured()
os.environ['MULTIPROSHOP_DATAFORSEO_LOGIN'], os.environ['MULTIPROSHOP_DATAFORSEO_PASSWORD'] = 'l', 'p'
assert dfs.configured()
client = dfs.DataForSEO(poll=0)
assert client.trends(['micro cravate', 'support tablette']) == {'micro cravate': 50, 'support tablette': 10}
items = client.amazon('micro cravate')
assert [i['ref'] for i in items] == ['B01', 'B02'] and items[0]['bought_month'] == 2000 and items[0]['price'] == 19.99
assert items[1]['price'] is None  # prix en dollars : pas comparé
assert sent[1][2][0]['se_domain'] == 'amazon.fr' and sent[1][2][0]['priority'] == 2
assert round(client.cost, 3) == 0.014
dfs.requests.request = lambda *a, **k: Resp({'status_code': 40100}, 401)
try:
    client.trends(['x']); raise AssertionError('401 non signalé')
except dfs.DataForSEOError as e:
    assert 'refusés' in str(e)
for k in ('MULTIPROSHOP_DATAFORSEO_LOGIN', 'MULTIPROSHOP_DATAFORSEO_PASSWORD'):
    os.environ.pop(k)
print('DataForSEO OK')

# --- Faux CJ : liste par mot-clé, fiches, stock ---
CJ = {  # pid : (nom, boutiques CJ, prix d'achat $, poids g)
    'P1': ('Wireless Lavalier Microphone for Phone', 900, '4.5', '120'),
    'P4': ('Lavalier Mic Heavy Kit', 700, '5', '5000'),
    'P2': ('Lapel Mic Clip USB-C', 500, '6', '80'),
    'P3': ('Phone Case Silicone', 9999, '2', '50'),  # best-seller CJ hors sujet
}
api = Api.__new__(Api)
def cj_request(method, endpoint, params=None, json=None, **kw):
    if endpoint == 'product/listV2':
        if 'lavalier' not in params['keyWord']:
            return {'result': True, 'data': {'content': [{'productList': [
                {'id': 'P3', 'nameEn': CJ['P3'][0], 'bigImage': 'https://c/P3.jpg', 'listedNum': 9999}]}]}}
        return {'result': True, 'data': {'content': [{'productList': [
            {'id': pid, 'nameEn': v[0], 'bigImage': f'https://c/{pid}.jpg', 'listedNum': v[1]} for pid, v in CJ.items()]}]}}
    if endpoint == 'product/query':
        pid = params['pid']; name, _, price, weight = CJ[pid]
        return {'result': True, 'data': {'pid': pid, 'productNameEn': name, 'productSku': f'CJ{pid}', 'sellPrice': price,
                'productImage': [f'https://c/{pid}-{i}.jpg' for i in range(5)], 'productWeight': weight,
                'categoryName': 'Studio', 'description': '<p>EN</p>',
                'variants': [{'vid': f'{pid}V1', 'variantKey': 'Black', 'variantSellPrice': price, 'variantWeight': weight}]}}
    if endpoint == 'product/sourcing/create':
        return {'result': True, 'data': {'cjSourcingId': '77'}}
    return {'result': False}
api._make_request = cj_request
api.get_stock = lambda variants, enough=None, max_variants=10: {'total': 200, 'france': 0}
import routes.admin as adm
adm._cj_api = lambda: api

class FakeWeb:
    cost = 0.02
    def trends(self, kws): return {k: (50 if 'cravate' in k else 12) for k in kws}
    def amazon(self, kw):
        return [{'kind': 'amazon', 'ref': f'A-{kw[:5]}', 'title': f'{kw} Amazon', 'url': 'https://amazon.fr/dp/X',
                 'image': 'https://m/a.jpg', 'price': 20.0, 'rating': 4.5, 'votes': 300, 'bought_month': 1000},
                {'kind': 'amazon', 'ref': f'B-{kw[:5]}', 'title': 'mal noté', 'price': 5.0, 'rating': 3.1, 'votes': 9}]
    def shopping(self, kw):
        return [{'kind': 'shopping', 'ref': f'G-{kw[:5]}', 'title': f'{kw} Google', 'url': 'https://g/x',
                 'image': 'https://m/g.jpg', 'price': 24.0, 'rating': None, 'votes': None}]
research._web = lambda: FakeWeb()

with app.app_context():
    db.drop_all(); db.create_all(); cache.clear()
    from models.storefront import ensure_defaults
    ensure_defaults()
    c = Category(name='Studio', slug='st', level=1, is_active=True, visible=True); db.session.add(c); db.session.flush()
    db.session.add(Product(name='Micro-cravate USB-C', slug='mic', sku='M1', price=14.9, cost_price=5.5, stock=50,
                           category_id=c.id, is_active=True, published=True, cj_pid='P2', projects='serenis'))
    r = Role(name='admin'); db.session.add(r); db.session.flush()
    u = User(username='boss', email='b@x.com', role_id=r.id); u.set_password('pw123456'); db.session.add(u)
    db.session.commit()

assert app.test_client().get('/admin/recherche-produits').status_code in (302, 401, 403)
cl = app.test_client()
cl.post('/auth/admin-login', data={'username': 'boss', 'password': 'pw123456'})
h = cl.get('/admin/recherche-produits').get_data(as_text=True)
assert 'Nouvelle veille' in h and 'DataForSEO pas encore branché' in h, h[-2000:]

lines = ('Micro-cravate sans fil | micro cravate | wireless lavalier microphone | lavalier|lapel, mic\n'
         'Support tablette | support tablette | tablet stand | tablet')
r = cl.post('/admin/recherche-produits', data={'name': 'DIGITA son', 'storefront': 'digita', 'lines': lines,
                                                'web': '1', 'active': '1', 'per_query': '2', 'max_examined': '6'})
assert r.status_code == 302, r.status_code
with app.app_context():
    w = ResearchWatch.query.one(); wid = w.id
    assert w.get_queries()[0]['must'] == ['lavalier|lapel', 'mic'] and w.storefront == 'digita'
cl.post(f'/admin/recherche-produits/{wid}/lancer')
with app.app_context():
    w = db.session.get(ResearchWatch, wid)
    res = {(x.kind, x.ref): x for x in w.results}
    assert ('cj', 'P3') not in res and ('cj', 'P4') not in res, list(res)  # hors sujet ; trop lourd
    p1, p2 = res[('cj', 'P1')], res[('cj', 'P2')]
    assert p1.verdict == p2.verdict == 'dispo' and p1.listed == 900
    assert p1.price_eur == 10.9 and p1.cost_eur == 4.14, (p1.price_eur, p1.cost_eur)  # 4,50 $ × 0,92 × 2,5 → 10,90 €
    assert p1.market_price == 20.0 and 'web 20.00 € (-4' in p1.note and p1.trend == 50, (p1.market_price, p1.note)
    assert 'déjà dans MPS' in p2.note and p2.product_id
    assert res[('amazon', 'A-micro')].verdict == 'info'  # CJ en a : simple repère
    assert ('amazon', 'B-micro') not in res  # mal noté
    assert res[('amazon', 'A-suppo')].verdict == res[('shopping', 'G-suppo')].verdict == 'a_sourcer'
    assert w.last_run_note.startswith('2 dispo chez CJ, 2 à sourcer ; DataForSEO 0.020 $') and 'poids 1' in w.last_run_note, w.last_run_note
    p1_id, p2_id, src_id, amz_id = p1.id, p2.id, res[('amazon', 'A-suppo')].id, res[('shopping', 'G-suppo')].id
h = cl.get(f'/admin/recherche-produits/{wid}').get_data(as_text=True)
assert 'Wireless Lavalier' in h and 'Support tablette' in h and 'Importer en brouillon' in h and 'Sourcing CJ' in h, h[-3000:]
assert 'Google Trends 50/100' in h and '900 boutiques CJ' in h
print('veille OK')

# Import en brouillon dans DIGITA ; le produit déjà en ligne reçoit seulement la vitrine
cl.post(f'/admin/recherche-produits/resultat/{p1_id}', data={'action': 'import'})
cl.post(f'/admin/recherche-produits/resultat/{p2_id}', data={'action': 'import'})
with app.app_context():
    new = Product.query.filter_by(cj_pid='P1').one()
    assert not new.is_active and new.published_at is None and new.projects == 'digita', (new.is_active, new.projects)
    assert new.name == 'Micro-cravate sans fil' and new.price == 10.9 and new.cost_price == 4.14
    old = Product.query.filter_by(cj_pid='P2').one()
    assert old.name == 'Micro-cravate USB-C' and old.is_active and old.projects == 'digita,serenis'
    assert db.session.get(ResearchResult, p1_id).verdict == 'importe' and db.session.get(ResearchResult, p1_id).product_id == new.id
# Sourcing CJ d'un produit vu sur Amazon ; on écarte celui de Google
cl.post(f'/admin/recherche-produits/resultat/{src_id}', data={'action': 'sourcing'})
cl.post(f'/admin/recherche-produits/resultat/{amz_id}', data={'action': 'ecarter'})
with app.app_context():
    s = CjSourcing.query.one()
    assert s.cj_sourcing_id == '77' and 'Recherche MPS « Support tablette »' in s.remark and 'prix constaté 20.00 €' in s.remark
    assert db.session.get(ResearchResult, src_id).verdict == 'sourcing'
# Second passage : les choix faits à la main restent
cl.post(f'/admin/recherche-produits/{wid}/lancer')
with app.app_context():
    assert db.session.get(ResearchResult, p1_id).verdict == 'importe'
    assert db.session.get(ResearchResult, src_id).verdict == 'sourcing'
    assert db.session.get(ResearchResult, amz_id).verdict == 'ecarte'
    assert ResearchResult.query.count() == 6, ResearchResult.query.count()  # pas de doublon
h = cl.get(f'/admin/recherche-produits/{wid}?voir=ecarte').get_data(as_text=True)
assert 'Reprendre' in h and 'support tablette Google' in h
cl.post(f'/admin/recherche-produits/resultat/{amz_id}', data={'action': 'restore'})
with app.app_context():
    assert db.session.get(ResearchResult, amz_id).verdict == 'a_sourcer'
print('import, sourcing et écart OK')

# Sans DataForSEO : CJ seul, et la note le dit
research._web = lambda: None
with app.app_context():
    w = db.session.get(ResearchWatch, wid)
    note = research.run_watch(w, cj_api=api)
    assert 'web non comparé (DataForSEO non branché)' in note, note

# Claude complète une ligne qui n'a que le titre ; reprise de la fiche de DIGITA
import services.ai_copy as ai
ai._generate = lambda system, prompt, max_tokens=0: 'Voici : [{"fr": "Lampe de bureau LED", "web": "lampe bureau led", "q": "led desk lamp", "must": ["desk lamp|table lamp"]}]'
cl.post('/admin/recherche-produits', data={'name': 'ALIAS bureau', 'storefront': 'tonyalpha', 'claude': '1', 'active': '1',
                                            'lines': 'Lampe de bureau LED'})
cl.post('/admin/recherche-produits', data={'name': 'DIGITA fiche', 'storefront': 'digita', 'from_brief': '1', 'active': '1'})
with app.app_context():
    q = ResearchWatch.query.filter_by(name='ALIAS bureau').one().get_queries()
    assert q == [{'fr': 'Lampe de bureau LED', 'web': 'lampe bureau led', 'q': 'led desk lamp', 'must': ['desk lamp|table lamp']}], q
    brief = json.load(open('scripts/vitrines/digita.json', encoding='utf-8'))
    n = sum(len(g['queries']) for g in brief['groups'])
    assert len(ResearchWatch.query.filter_by(name='DIGITA fiche').one().get_queries()) == n
    out = research.run_active()
    assert len(out) == 3
# Réglages enregistrés, puis suppression
cl.post(f'/admin/recherche-produits/{wid}', data={'name': 'DIGITA son', 'storefront': 'digita', 'lines': lines,
                                                   'min_cost': '2', 'max_cost': 'abc', 'france_only': '1'})
with app.app_context():
    w = db.session.get(ResearchWatch, wid)
    assert w.get_criteria()['min_cost'] == 2 and w.get_criteria()['max_cost'] == 45.0 and w.get_criteria()['france_only']
    assert not w.web and not w.active
cl.post(f'/admin/recherche-produits/{wid}', data={'action': 'delete'})
with app.app_context():
    assert db.session.get(ResearchWatch, wid) is None and Product.query.filter_by(cj_pid='P1').count() == 1
print('Claude, fiche et réglages OK')
