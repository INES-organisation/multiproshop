import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); sys.path.insert(0, ROOT); os.chdir(ROOT)
import requests
from services.api_providers import cj_dropshipping_optimized as cj

calls = []


class Resp:
    status_code = 200
    text = '{}'

    def json(self):
        return {'result': True, 'code': 200, 'data': {'orderId': 'CJ1'}}


requests.request = lambda method, url, **kw: calls.append((method, url, kw)) or Resp()
api = cj.CJDropshippingApiOptimized(email='e', password='p')
api.get_access_token = lambda: (_ for _ in ()).throw(AssertionError('pas de jeton CJ local via INES'))

os.environ.update(CJ_VIA_INES='1', INES_API_URL='https://ines.test/', INES_API_KEY='k')
out = api._make_request('POST', '/shopping/order/createOrder', json={'orderNumber': 'MPS-1'})
method, url, kw = calls[-1]
assert out['data']['orderId'] == 'CJ1'
assert url == 'https://ines.test/api/v1/external/cj/api/shopping/order/createOrder', url
assert kw['params'] == {'site': 'multiproshop'} and kw['json'] == {'orderNumber': 'MPS-1'}
assert kw['headers']['Authorization'] == 'Bearer k'

api._make_request('GET', 'product/list', params={'pageNum': 2})
assert calls[-1][2]['params'] == {'pageNum': 2, 'site': 'multiproshop'} and calls[-1][2]['json'] is None

Resp.status_code = 429
assert api._make_request('GET', 'product/list') is None  # file du hub saturée : échec propre
print('CJ via le hub INES OK')
