"""Litiges CJ : lecture via l'API et alertes quand un litige apparaît ou change d'état"""
import logging

logger = logging.getLogger(__name__)


def _first(d, *keys):
    for k in keys:
        if d.get(k) not in (None, ''):
            return d[k]
    return None


def normalize(raw):
    """Champs utiles d'un litige, quel que soit le nom exact renvoyé par CJ"""
    from models.order import Order
    order_ref = _first(raw, 'orderId', 'orderCode', 'orderNumber', 'cjOrderId')
    order = Order.query.filter_by(cj_order_id=str(order_ref)).first() if order_ref else None
    return {
        'id': _first(raw, 'id', 'disputeId'),
        'order_ref': order_ref,
        'order': order,
        'reason': _first(raw, 'disputeReason', 'reason', 'disputeReasonName'),
        'status': _first(raw, 'status', 'disputeStatus', 'statusName'),
        'amount': _first(raw, 'money', 'refundAmount', 'replacementAmount', 'amount'),
        'resolution': _first(raw, 'finallyDeal', 'expectType', 'resultType', 'dealType'),
        'created': _first(raw, 'createDate', 'createTime', 'createdAt'),
        'raw': raw,
    }


def fetch(api, page=1, size=20, order_id=None):
    data = api.get_disputes(page=page, size=size, order_id=order_id)
    if data is None:
        return None
    return {'items': [normalize(r) for r in data['list'] if isinstance(r, dict)], 'total': data['total']}


def check_new(api, pages=3):
    """Notifie chaque litige nouveau ou dont l'état a changé (dédoublonné par id et état)"""
    from services.notifications import notify
    count = 0
    for page in range(1, pages + 1):
        data = fetch(api, page=page, size=50)
        if not data or not data['items']:
            break
        for d in data['items']:
            if d['id'] is None:
                continue
            n = notify('dispute', f"Litige CJ {d['id']} : {d['status'] or 'mis à jour'}",
                       ' — '.join(str(x) for x in (d['reason'], d['order_ref'] and f"commande CJ {d['order_ref']}") if x),
                       url='/admin/litiges', level='warning', dedupe=f"dispute:{d['id']}:{d['status']}")
            count += 1 if n else 0
        if len(data['items']) < 50:
            break
    return count
