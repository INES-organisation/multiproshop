import os, sys, time
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); sys.path.insert(0, ROOT); os.chdir(ROOT)
import app as appmod
from extensions import cache
app = appmod.create_app('testing')
import services.api_providers.cj_dropshipping_optimized as m
calls = []
class Resp:
    status_code = 200
    def __init__(self, payload): self.payload = payload; self.text = '{}'
    def json(self): return self.payload
def fake_post(url, **k):
    calls.append(url)
    return Resp({'result': True, 'data': {'accessToken': 'TOK', 'accessTokenExpiryDate': None}})
m.requests.post = fake_post
with app.app_context():
    cache.clear()
    with app.test_request_context('/'):
        a = m.CJDropshippingApiOptimized(email='e', password='p')
        assert a.fail_fast and a.get_access_token() == 'TOK' and len(calls) == 1
    # autre processus : mémoire vide, le token vient du cache partagé
    m._memory_cache.update(access_token=None, token_expires_at=0, last_auth_call=0)
    with app.test_request_context('/'):
        assert m.CJDropshippingApiOptimized(email='e', password='p').get_access_token() == 'TOK' and len(calls) == 1
    # token perdu + auth récente : on échoue vite au lieu d'attendre 5 min
    cache.delete('cj:access_token'); m._memory_cache.update(access_token=None, token_expires_at=0)
    t = time.time()
    with app.test_request_context('/'):
        assert m.CJDropshippingApiOptimized(email='e', password='p').get_access_token() is None
    assert time.time() - t < 1 and len(calls) == 1
print('TOUT OK token partagé')
