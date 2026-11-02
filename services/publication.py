"""Vérifications faites à la mise en ligne d'un produit CJ.

1. Stock réel des variantes actives, relu chez CJ (les stocks des produits jamais publiés datent de l'import).
2. Livraison vers la France et La Réunion, avec enregistrement des tarifs de port.
3. À la première publication : prix de chaque variante calculé avec la grille ci-dessous à partir du coût CJ.

Chaque appel CJ prend un créneau partagé (environ 1,3 s) : on borne le nombre de variantes relues
et on respecte une échéance pour rester sous le délai de la requête web.
"""
import json
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


def _clean_images(images):
    out = []
    for im in images or []:
        if isinstance(im, str) and im.strip().startswith('['):
            try:
                parsed = json.loads(im)
                out.extend(parsed if isinstance(parsed, list) else [im])
            except ValueError:
                out.append(im)
        elif im:
            out.append(im)
    seen = set()
    return [u for u in out if not (u in seen or seen.add(u))]


def enrich(product, api):
    """Complète la fiche depuis CJ (product/query, 1 appel) sans écraser ce qui a été saisi en boutique :
    description, photos, poids, matière, données brutes (noms d'options), coût par variante, variantes
    ajoutées chez CJ (inactives si le produit en avait déjà), couleur/taille réparées depuis la clé CJ.
    Renvoie la fiche CJ, ou None si CJ ne répond pas."""
    from models.product_variant import ProductVariant
    from utils.variant_keys import product_key_names, repair_variant, split_variant_key
    try:
        details = api.get_product_details(product.cj_pid)
    except Exception as e:
        logger.warning(f'[Publication] Fiche CJ {product.cj_pid} illisible : {e}')
        details = None
    if not details:
        return None
    if details.get('description') and not (product.description or '').strip():
        product.description = details['description']
    images = _clean_images(details.get('images'))
    if images and not product.get_images_list():
        product.set_images_list(images)
    if images and not product.image_url:
        product.image_url = images[0]
    if details.get('weight') and not product.weight:
        try:
            product.weight = float(details['weight'])
        except (TypeError, ValueError):
            pass
    if details.get('material') and not getattr(product, 'material', None):
        product.material = details['material']
    if details.get('raw_data'):
        product.cj_raw_data = json.dumps(details['raw_data'], default=str, ensure_ascii=False)
    names = product_key_names(product)
    existing = {v.cj_vid: v for v in ProductVariant.query.filter_by(product_id=product.id).all() if v.cj_vid}
    had_variants = bool(existing)
    for cj in details.get('variants') or []:
        vid = cj.get('vid')
        if not vid:
            continue
        raw = {k: cj.get(k) for k in ('vid', 'key', 'sku', 'price', 'suggested_price', 'image', 'weight', 'variantNameEn')}
        variant = existing.get(vid)
        if variant is None:
            parsed = split_variant_key(cj.get('key'), names) or (cj.get('key') or None, None)
            variant = ProductVariant(product_id=product.id, cj_vid=vid, variant_key=cj.get('key') or None,
                                     color=parsed[0], size=parsed[1], price=None, stock=0,
                                     image_url=cj.get('image') or product.image_url, sku=cj.get('sku') or None,
                                     weight=cj.get('weight') or None, active=not had_variants)
            from extensions import db
            db.session.add(variant)
        else:
            variant.variant_key = variant.variant_key or cj.get('key') or None
            variant.sku = variant.sku or cj.get('sku') or None
            variant.weight = cj.get('weight') or variant.weight
        variant.cj_raw_data = json.dumps(raw, ensure_ascii=False)  # coût CJ à jour (models.cart.cost_price)
        repair_variant(variant, names)
    from extensions import db
    db.session.flush()
    return details


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
    if enrich(product, api) is None:
        logger.info(f'[Publication] Fiche CJ indisponible pour {product.cj_pid} : publication sans enrichissement')
    problem = refresh_stock(product, api, deadline)
    if problem:
        return problem
    problem = check_delivery(product, _shipping(), deadline)
    if problem:
        return problem
    if reprice and product.published_at is None:
        apply_grid(product)
    return None


PENDING_KEY = 'copy_pending:%d'


def copy_pending(product_id):
    from extensions import cache
    try:
        return bool(cache.get(PENDING_KEY % product_id))
    except Exception:
        return False


def _queue(product_id):
    from tasks.publication_tasks import write_and_publish as task
    task.delay(product_id)


def go_live(product):
    """À appeler quand les vérifications sont passées. Première publication d'une fiche encore en anglais :
    le produit reste hors ligne le temps que Claude rédige la fiche (tâche de fond, ~30 s), puis passe en
    ligne. Renvoie 'live' ou 'queued'."""
    from services import ai_copy
    from extensions import cache
    if product.published_at is None and ai_copy.enabled() and not ai_copy.looks_french(product):
        if not copy_pending(product.id):
            cache.set(PENDING_KEY % product.id, 1, timeout=600)
            try:
                _queue(product.id)
            except Exception as e:
                cache.delete(PENDING_KEY % product.id)
                logger.error(f'[Publication] File de tâches indisponible : {e}')
                raise
        return 'queued'
    if product.published_at is None:
        from services.translate import translate_options
        translate_options(product)  # libellés encore en anglais : DeepL s'il est configuré dans INES
        product.published_at = datetime.utcnow()
    product.is_active = True
    return 'live'


def write_and_publish(product_id):
    """Tâche de fond : rédaction par Claude, puis mise en ligne. En cas d'échec, le produit reste hors ligne
    et une notification explique quoi faire."""
    from extensions import db, cache
    from models.product import Product
    from services import ai_copy
    from services.notifications import notify
    product = db.session.get(Product, product_id)
    if product is None:
        return {'error': 'produit introuvable'}
    url = f'/admin/products/edit/{product.id}'
    from services.translate import translate_options
    options_done = translate_options(product) is not None  # DeepL d'abord pour les libellés, Claude sinon
    try:
        data = ai_copy.generate(product, with_options=not options_done)
        ai_copy.apply(product, data)
    except Exception as e:
        db.session.rollback()
        notify('publication', f'Non publié : {product.name[:80]}',
               f'Rédaction de la fiche impossible ({e}). Rédigez le titre et la description en français dans la fiche, '
               'puis publiez-le : il passera en ligne sans nouvelle rédaction.', url=url, level='warning',
               dedupe=f'copy:{product.id}')
        cache.delete(PENDING_KEY % product.id)
        return {'error': str(e)}
    product.is_active = True
    product.published_at = product.published_at or datetime.utcnow()
    db.session.commit()
    cache.delete(PENDING_KEY % product.id)
    cache.delete('menu_category_ids')
    try:
        cache.delete(f'view//products/{product.id}')  # Flask-Caching ajoute lui-même le préfixe flask_cache_
    except Exception:
        pass
    notify('publication', f'En ligne : {product.name[:80]}', 'Fiche rédigée en français par Claude, à relire si besoin.',
           url=url, level='info')
    return {'published': product.id}
