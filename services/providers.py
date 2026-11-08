"""Fournisseurs : chaque produit a le sien (product.provider, vide = CJ).

Le port se calcule fournisseur par fournisseur puis s'additionne, et chaque fournisseur reçoit sa
part de la commande payée. Brancher un fournisseur = une fonction dans QUOTERS (tarifs de port) et
une dans PLACERS (passer la commande). Tant qu'il n'y est pas, ses produits n'ont pas de port
proposé (donc ne se vendent pas) et une commande déjà payée est signalée à passer à la main.
"""
import logging

logger = logging.getLogger(__name__)

DEFAULT = 'cj'
LABELS = {'cj': 'CJ Dropshipping', 'vidaxl': 'vidaXL', 'bigbuy': 'BigBuy', 'syncee': 'Syncee',
          'printful': 'Printful'}


def of(product):
    return (getattr(product, 'provider', None) or DEFAULT) if product is not None else DEFAULT


def clean(value):
    value = (value or '').strip().lower()
    return value if value in LABELS else DEFAULT


def group(items, product=lambda i: i.get('product') if isinstance(i, dict) else i.product):
    """{fournisseur: [articles]} dans l'ordre du panier"""
    groups = {}
    for item in items:
        groups.setdefault(of(product(item)), []).append(item)
    return groups


# Méthode d'un panier à plusieurs fournisseurs : « cj:CJPacket|bigbuy:GLS », une part par fournisseur.
# Panier à un seul fournisseur : le code du fournisseur tel quel (rien ne change pour CJ seul).
def method_for(code, provider):
    if not code or '|' not in code:
        return code
    parts = dict(p.split(':', 1) for p in code.split('|') if ':' in p)
    return parts.get(provider)


def combine(per_provider):
    """{fournisseur: [méthodes]} → une méthode : la moins chère de chaque fournisseur, prix additionnés.
    ponytail: une seule combinaison proposée (la moins chère) ; proposer aussi la plus rapide si besoin."""
    picks = {name: min(methods, key=lambda m: m['price']) for name, methods in per_provider.items()}
    return [{
        'code': '|'.join(f"{name}:{m['code']}" for name, m in picks.items()),
        'name': ' + '.join(f"{LABELS.get(name, name)} : {m.get('name') or m['code']}" for name, m in picks.items()),
        'price': round(sum(float(m['price']) for m in picks.values()), 2),
        'delivery_time': ' / '.join(str(m.get('delivery_time') or '') for m in picks.values()),
        'parts': picks,
        'source': 'multi',
    }]


def _place_cj(order):
    from models.api_provider import ApiProvider
    from services.api_providers.cj_dropshipping_optimized import CJDropshippingProvider
    from services.cj_order_service import CjOrderService
    provider = ApiProvider.query.filter_by(name='CJ Dropshipping', is_active=True).first()
    if not provider:
        return {'success': False, 'message': 'Fournisseur CJ inactif ou introuvable.'}
    return CjOrderService(CJDropshippingProvider(provider=provider)).create_cj_order(order.id)


QUOTERS = {}  # 'cj' est calculé directement par ShippingService
PLACERS = {'cj': _place_cj}


def dispatch(order):
    """Après paiement : chaque fournisseur reçoit sa part. Une erreur n'annule jamais la commande payée."""
    from services.notifications import notify
    for name in group(order.order_items):
        label = LABELS.get(name, name)
        placer = PLACERS.get(name)
        try:
            result = placer(order) if placer else {'success': False, 'message': "Ce fournisseur n'est pas encore branché."}
        except Exception as e:  # noqa: BLE001 — la commande reste payée, à passer à la main
            result = {'success': False, 'message': str(e)}
        if not result.get('success'):
            logger.error("Commande %s non créée pour %s : %s", label, order.order_number, result.get('message'))
            notify('cj_order_error', f'Commande {label} à passer à la main : {order.order_number}',
                   result.get('message'), url=f'/admin/orders/{order.id}', level='danger')
