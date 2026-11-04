import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); sys.path.insert(0, ROOT); os.chdir(ROOT)
import app as appmod
from extensions import db, cache
app = appmod.create_app('testing'); appmod.app = app
import services.webhook_handler as wh
calls = []
wh.WebhookHandler.process_webhook = lambda self, data: calls.append(data) or {'success': True}
wh.WebhookHandler.log_webhook = lambda self, *a: None
with app.app_context():
    db.drop_all(); db.create_all()
cl = app.test_client()
body = {'messageId': 'm1', 'type': 'ORDER', 'params': {'orderId': 'X', 'orderStatus': 'SHIPPED'}}
os.environ['CJ_WEBHOOK_TOKEN'] = 's3cret'
assert cl.post('/webhooks/cj/message', json=body).status_code == 403
assert cl.post('/webhooks/cj/message?token=nope', json=body).status_code == 403 and not calls
assert cl.post('/webhooks/cj/message?token=s3cret', json=body).status_code == 200 and len(calls) == 1
assert cl.post('/webhooks/cj/message', json=body, headers={'X-CJ-Webhook-Token': 's3cret'}).status_code == 200 and len(calls) == 2
assert cl.post('/webhooks/cj/message', json=body, headers={'X-CJ-Webhook-Token': 'nope'}).status_code == 403
del os.environ['CJ_WEBHOOK_TOKEN']
assert cl.post('/webhooks/cj/message', json=body).status_code == 200 and len(calls) == 3  # pas encore configuré
print('webhook CJ : jeton exigé quand configuré OK')
