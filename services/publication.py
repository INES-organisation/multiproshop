"""Vérifications faites à la mise en ligne d'un produit CJ.

1. Stock réel des variantes actives, relu chez CJ (les stocks des produits jamais publiés datent de l'import).
2. Livraison vers la France et La Réunion, avec enregistrement des tarifs de port.
3. À la première publication : prix de chaque variante calculé avec la grille ci-dessous à partir du coût CJ.

Chaque appel CJ prend un créneau partagé (environ 1,3 s) : on borne le nombre de variantes relues
et on respecte une échéance pour rester sous le délai de la requête web.
"""
import logging
import math
import time
from datetime import datetime

logger = logging.getLogger(__name__)

STOCK_MAX_VARIANTS = 12
COUNTRIES = {'FR': 'en France', 'RE': 'à La Réunion'}
MIN_PRICE = 9.90


def grid_price(cost):
    """Prix de vente conseillé pour un coût CJ en euros : × 2,5 sous 10 €, × 2 jusqu'à 30 €, × 1,6 au-delà,
    arrondi au x,90 € supérieur, 9,90 € minimum. Le prix ne baisse jamais quand le coût monte."""
    if cost < 10:
        raw = cost * 2.5
    elif cost < 30:
        raw = max(cost * 2.0, 25.0)   # pas de prix plus bas qu'un article à 9,99 € de coût
    else:
        raw = max(cost * 1.6, 60.0)   # idem au passage des 30 €
    raw = max(raw, MIN_PRICE)
    price = math.floor(raw) + 0.90
    if price + 1e-9 < raw:
        price += 1
    return round(price, 2)


def apply_grid(product):
    """Prix de toutes les variantes actives d'après leur coût ; le produit affiche la moins chère"""
    from models.cart import cost_price
    prices = []
    for variant in _active_variants(product):
        cost = cost_price(product, variant)
        if cost:
            variant.price = grid_price(cost)
            prices.append(variant.price)
    if prices:
        product.price = min(prices)
    elif product.cost_price:
        product.price = grid_price(product.cost_price)
    if product.compare_price and product.price and product.compare_price <= product.price:
        product.compare_price = None


def _active_variants(product):
    from models.product_variant import ProductVariant
    return ProductVariant.query.filter_by(product_id=product.id, active=True).order_by(ProductVariant.id).all()


def _api():
    from routes.admin_cj_sync import get_cj_api
    return get_cj_api()


def _shipping():
    from services.shipping_service import ShippingService
    return ShippingService()


def _late(deadline):
    return deadline is not None and time.time() > deadline


def refresh_stock(product, api, deadline=None):
    """Relit le stock CJ des variantes actives. Renvoie un motif de refus, ou None."""
    variants = [v for v in _active_variants(product) if v.cj_vid]
    if not variants:
        return None  # rien à relire (produit sans variante CJ) : on garde le stock connu
    answered = 0
    for variant in variants[:STOCK_MAX_VARIANTS]:
        if _late(deadline):
            break
        warehouses = api.get_variant_inventory(variant.cj_vid)
        if warehouses is None:
            continue
        variant.stock = sum(w['total'] for w in warehouses)
        answered += 1
    if not answered:
        return "CJ n'a pas répondu pour le stock (limite d'appels atteinte ?). Réessayez dans une minute."
    product.stock = sum(max(v.stock or 0, 0) for v in variants)
    product.stock_checked = True
    product.synced_at = datetime.utcnow()
    if product.stock <= 0:
        return 'en rupture de stock chez CJ.'
    return None


def check_delivery(product, shipping, deadline=None):
    """Vérifie la livraison FR et RE et enregistre les tarifs. CJ muet = pas de refus (tarif recalculé lundi)."""
    from services.shipping_service import ShippingService
    missing = []
    for country, label in COUNTRIES.items():
        if _late(deadline):
            break
        methods = shipping.refresh_product_rate(product, country)
        if methods is None:
            continue
        ShippingService.store_rate(product.id, country, methods, commit=False)
        if not methods:
            missing.append(label)
    if missing:
        return 'CJ ne livre pas ce produit ' + ' ni '.join(missing) + '.'
    return None


def prepare(product, deadline=None, reprice=True):
    """Prépare un produit CJ à sa mise en ligne. Renvoie un motif de refus, ou None si tout est bon."""
    if deadline is None:
        deadline = time.time() + 45  # requête web : gunicorn coupe à 60 s
    if _late(deadline):
        return 'vérifications CJ non faites faute de temps : relancez la publication de ce produit.'
    try:
        api = _api()
    except Exception as e:
        logger.warning(f'[Publication] API CJ indisponible : {e}')
        return 'API CJ indisponible, impossible de vérifier le stock. Réessayez plus tard.'
    problem = refresh_stock(product, api, deadline)
    if problem:
        return problem
    problem = check_delivery(product, _shipping(), deadline)
    if problem:
        return problem
    if reprice and product.published_at is None:
        apply_grid(product)
    return None
