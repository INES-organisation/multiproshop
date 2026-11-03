import os, sys, time, threading
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); sys.path.insert(0, ROOT); os.chdir(ROOT)
import app as appmod
from extensions import cache
app = appmod.create_app('testing')
import services.api_providers.cj_dropshipping_optimized as m
m._memory_cache['min_interval'] = 0
stamps = []
class R:
    status_code = 200; text = "{\"result\":true,\"data\":[]}"
    def json(self): return {"result": True, "data": []}
def fake(url, **k):
    stamps.append(time.time()); return R()
m.requests.get = fake
with app.app_context():
    cache.clear(); cache.set('cj:access_token', {'token': 'T', 'expires': time.time() + 999}, 999)
def worker():
    with app.test_request_context('/'):
        assert m.CJDropshippingApiOptimized(email='e', password='p')._make_request('GET', 'x') is not None
ts = [threading.Thread(target=worker) for _ in range(5)]
t0 = time.time(); [t.start() for t in ts]; [t.join() for t in ts]
secs = sorted(int(s) for s in stamps)
assert len(stamps) == 5 and len(set(secs)) == 5, secs
print('5 appels en %.1fs, un par seconde : OK' % (time.time() - t0))

# Chemin Redis simulé : écart réel >= 1,1 s
import threading as th
class FakeRedis:
    def __init__(self): self.exp = 0; self.lock = th.Lock()
    def set(self, k, v, px=None, nx=False):
        with self.lock:
            now = time.time()
            if nx and now < self.exp: return False
            self.exp = now + px / 1000; return True
with app.app_context():
    cache.cache._write_client = FakeRedis()
stamps.clear()
ts = [threading.Thread(target=worker) for _ in range(4)]
[t.start() for t in ts]; [t.join() for t in ts]
st = sorted(stamps); gaps = [b - a for a, b in zip(st, st[1:])]
assert len(st) == 4 and min(gaps) >= 1.09, gaps
print('écart réel minimal %.2fs : OK' % min(gaps))
with app.app_context():
    del cache.cache._write_client

# Même panier demandé en même temps : un seul appel CJ
import services.shipping_service as ss
n = []
class FakeApi:
    def calculate_shipping(self, products, country, start_country='CN'):
        n.append(1); time.sleep(1); return [{'logisticName': 'A', 'logisticPrice': 5, 'logisticAging': '7-9'}]
res = []
def w2():
    with app.app_context():
        svc = ss.ShippingService.__new__(ss.ShippingService); svc.cj_api = FakeApi()
        res.append(svc._cart_freight([{'cj_vid': 'V9', 'quantity': 1}], 'FR'))
ts = [threading.Thread(target=w2) for _ in range(5)]
[t.start() for t in ts]; [t.join() for t in ts]
assert len(n) == 1 and all(r and r[0]['price'] == 4.6 for r in res), (n, res)
print('requêtes simultanées regroupées : OK')
