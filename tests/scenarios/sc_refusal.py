import os, sys, time
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); sys.path.insert(0, ROOT); os.chdir(ROOT)
import app as appmod
from extensions import cache
app = appmod.create_app('testing')
import services.api_providers.cj_dropshipping_optimized as m
class R:
    def __init__(s, code, body): s.status_code=code; s.text=body
    def json(s):
        import json; return json.loads(s.text)
seq = [R(429, '{"code":1600200}'), R(200, '{"code":200,"result":true,"data":[1]}')]
times = []
def fake(url, **k):
    times.append(time.time()); return seq.pop(0)
m.requests.post = fake
m.CJDropshippingApiOptimized.REFUSAL_PAUSE = 2
with app.app_context():
    cache.clear()
    api = m.CJDropshippingApiOptimized.__new__(m.CJDropshippingApiOptimized)
    api.base_url='http://x'; api.dev_key=None; api.verify_ssl=True; api.timeout=5; api.fail_fast=False
    api.get_access_token = lambda: 'T'
    m._memory_cache['min_interval'] = 0
    t0=time.time(); d = api._make_request('POST', 'logistic/freightCalculate', json={})
    assert d and d['data']==[1], d
    gap = times[1]-times[0]; assert 1.9 < gap < 4, gap
    print(f'tâche de fond : refus puis reprise après {gap:.1f}s OK')
    # une requête web pendant la pause abandonne tout de suite
    api._block(2); api.fail_fast=True; seq.append(R(200,'{}'))
    t=time.time(); assert api._make_request('POST','x', json={}) is None and time.time()-t < 0.5
    print('requête web pendant la pause : abandon immédiat OK')
