"""
API partenaires — /api/partner (04/11/2026)

Les sites de l'écosystème WAO (tonyalpha80.com…) vendent le catalogue MultiProShop chez eux :
le client choisit, paie et suit sa commande sur le site partenaire, MultiProShop reste la boutique
qui encaisse (Stripe d'INES), passe la commande CJ (hub CJ d'INES) et envoie les e-mails.

- GET  /api/partner/catalogue      produits publiés (public, mis en cache par le partenaire)
- GET  /api/partner/products/<id>  fiche produit avec variantes (public)
- POST /api/partner/shipping       méthodes de livraison pour un panier (jeton)
- POST /api/partner/orders         commande en attente + session de paiement (jeton)
- POST /api/partner/orders/confirm validation au retour du paiement (jeton)
- GET  /api/partner/orders         commandes d'un client du partenaire (jeton)
- POST /api/partner/newsletter     inscription à la newsletter, code de bienvenue par e-mail (jeton)

Seuil de livraison offerte propre à un site : FREE_SHIPPING_THRESHOLD_<SITE> (sinon celui de MPS).
Le port n'est offert que si la marge du panier reste positive (routes.cart._with_free_shipping).
Codes promo : « coupon_code » dans /shipping et /orders, mêmes règles que le panier MPS.

Jeton : en-tête « Authorization: Bearer … », variable PARTNER_TOKEN_<SITE> (saisie dans INES →
/admin/integrations sous MULTIPROSHOP_PARTNER_TOKEN_<SITE>, ex. MULTIPROSHOP_PARTNER_TOKEN_TONYALPHA).
Les prix, la livraison et le montant à payer sont toujours recalculés ici, jamais repris du partenaire.
"""
import hmac
import os
from functools import wraps

from flask import Blueprint, current_app, g, jsonify, request
from sqlalchemy import literal, or_

from routes.api_products import _PROJECT

from extensions import db
from models.category import Category
from models.order import Order, OrderItem
from models.product import Product
from models.product_variant import ProductVariant

partner_api = Blueprint('partner_api', __name__, url_prefix='/api/partner')

MAX_PER_PAGE = 60
MAX_ITEMS = 30
CUSTOMER_FIELDS = ('first_name', 'last_name', 'email', 'phone', 'address', 'city', 'postal_code')
SITE_LABELS = {'tonyalpha': 'tonyalpha80.com (ALIAS)', 'serenis': 'serenis.multiproshop.com'}


def _partners():
    """{site: jeton} depuis les variables PARTNER_TOKEN_<SITE>."""
    prefix = 'PARTNER_TOKEN_'
    return {k[len(prefix):].lower(): v for k, v in os.environ.items() if k.startswith(prefix) and len(v) >= 24}


def partner_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        auth = request.headers.get('Authorization', '')
        token = auth[7:] if auth.startswith('Bearer ') else ''
        for site, expected in _partners().items():
            if token and hmac.compare_digest(token, expected):
                g.partner_site = site
                return view(*args, **kwargs)
        return jsonify({'error': 'Jeton partenaire invalide'}), 401
    return wrapper


def _visible():
    return Product.query.filter(Product.published.is_(True), Product.is_active.is_(True))


def _stock(product, variant=None):
    """Même règle que le panier MPS : sans stock connu pour la variante (CJ ne le donne pas
    toujours), celui du produit."""
    if variant is not None and (variant.stock or 0) > 0:
        return variant.stock
    return product.stock or 0


def _variant_json(v):
    return {'id': v.id, 'color': v.color, 'size': v.size, 'price': v.price, 'stock': _stock(v.product, v),
            'image_url': v.image_url}


def _product_json(p, full=False):
    variants = [v for v in p.variants if v.active] if hasattr(p, 'variants') else []
    prices = [v.price for v in variants if v.price] or [p.price]
    data = {
        'id': p.id, 'slug': p.slug, 'name': p.name, 'short_description': p.short_description,
        'price': p.price, 'price_from': min(prices), 'compare_price': p.compare_price,
        'image_url': p.image_url, 'category': p.category.name_fr or p.category.name if p.category else None,
        'category_id': p.category_id, 'stock': p.stock or 0, 'has_variants': bool(variants),
        'rating_average': p.rating_average or 0, 'rating_count': p.rating_count or 0,
        'is_new': bool(p.is_new), 'is_on_sale': bool(p.is_on_sale),
    }
    if full:
        data.update(description=p.description, images=p.get_images_list(),
                    variants=[_variant_json(v) for v in variants])
    return data


def _free_shipping_threshold(site):
    raw = os.environ.get(f'FREE_SHIPPING_THRESHOLD_{(site or "").upper()}') if site else None
    try:
        return float(raw) if raw else current_app.config['FREE_SHIPPING_THRESHOLD']
    except ValueError:
        return current_app.config['FREE_SHIPPING_THRESHOLD']


def _reviews_json(p):
    """Avis déposés sur nos boutiques seulement (jamais ceux importés de CJ), les plus récents d'abord"""
    from models.product_review import ProductReview
    reviews = p.public_reviews.order_by(ProductReview.created_at.desc())
    count = reviews.count()
    latest = reviews.limit(10).all()
    average = round(sum(r.rating for r in reviews.all()) / count, 1) if count else 0
    return {'average': average, 'count': count, 'items': [{
        'author': r.author_name, 'rating': r.rating, 'title': r.title, 'comment': r.comment,
        'verified': bool(r.verified_purchase), 'images': r.get_images_list(),
        'date': (r.review_date or r.created_at).date().isoformat() if (r.review_date or r.created_at) else None,
    } for r in latest]}


def _in_project(query):
    """?project=<vitrine> : seulement les produits marqués pour cette vitrine (champ « Vitrines » de l'admin).
    Renvoie None si le nom est invalide."""
    project = (request.args.get('project') or '').strip().lower()
    if not project:
        return query
    if not _PROJECT.match(project):
        return None
    return query.filter((literal(',') + Product.projects + literal(',')).like(f'%,{project},%'))


@partner_api.route('/catalogue')
def catalogue():
    try:
        page = max(1, int(request.args.get('page', 1)))
        per_page = min(MAX_PER_PAGE, max(1, int(request.args.get('per_page', 24))))
        category_id = int(request.args['category']) if request.args.get('category') else None
    except ValueError:
        return jsonify({'error': 'Paramètres invalides'}), 400
    query = _in_project(_visible())
    if query is None:
        return jsonify({'error': 'Projet invalide'}), 400
    base = query  # compte par catégorie sur toute la vitrine, sans la recherche ni la catégorie choisie
    q = (request.args.get('q') or '').strip()[:100]
    if q:
        like = f'%{q}%'
        query = query.filter(or_(Product.name.ilike(like), Product.short_description.ilike(like)))
    if category_id:
        query = query.filter(Product.category_id == category_id)
    order = {'price_asc': Product.price.asc(), 'price_desc': Product.price.desc(),
             'popular': Product.sales_count.desc()}.get(request.args.get('sort'), Product.published_at.desc())
    pagination = query.order_by(order, Product.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    counts = dict(base.with_entities(Product.category_id, db.func.count(Product.id))
                  .order_by(None).group_by(Product.category_id).all())
    categories = [{'id': c.id, 'name': c.name_fr or c.name, 'count': counts[c.id]}
                  for c in Category.query.filter(Category.id.in_(list(counts))).all()]
    project = (request.args.get('project') or '').strip().lower()
    resp = jsonify({'products': [_product_json(p) for p in pagination.items], 'total': pagination.total,
                    'page': page, 'pages': pagination.pages,
                    'free_shipping': {'threshold': _free_shipping_threshold(project),
                                      'countries': list(current_app.config['FREE_SHIPPING_COUNTRIES'])},
                    'categories': sorted(categories, key=lambda c: c['name'])})
    resp.headers['Cache-Control'] = 'public, max-age=300'
    resp.headers['Access-Control-Allow-Origin'] = '*'  # données publiques, lisibles depuis le navigateur des vitrines
    return resp


@partner_api.route('/products/<int:product_id>')
def product(product_id):
    query = _in_project(_visible())
    p = query.filter(Product.id == product_id).first() if query is not None else None
    if not p:
        return jsonify({'error': 'Produit introuvable'}), 404
    return jsonify({**_product_json(p, full=True), 'reviews': _reviews_json(p)})


def _items(raw):
    """Lignes du panier partenaire → lignes MPS, avec le prix et le stock de la base."""
    if not isinstance(raw, list) or not 0 < len(raw) <= MAX_ITEMS:
        raise ValueError('Panier vide ou trop grand')
    items = []
    for line in raw:
        try:
            pid, qty = int(line['product_id']), int(line.get('quantity', 1))
            vid = int(line['variant_id']) if line.get('variant_id') else None
        except (KeyError, TypeError, ValueError):
            raise ValueError('Ligne de panier invalide')
        if not 0 < qty <= 20:
            raise ValueError('Quantité invalide')
        p = _visible().filter(Product.id == pid).first()
        if not p:
            raise ValueError(f'Produit {pid} indisponible')
        variant = None
        if vid:
            variant = ProductVariant.query.filter_by(id=vid, product_id=p.id, active=True).first()
            if not variant:
                raise ValueError(f'Variante indisponible pour « {p.name} »')
        elif any(v.active for v in p.variants):
            raise ValueError(f'Choisissez une option pour « {p.name} »')
        stock = _stock(p, variant)
        if stock < qty:
            raise ValueError(f'Stock insuffisant pour « {p.name} »')
        price = variant.price if variant and variant.price else p.price
        items.append({'product': p, 'variant': variant, 'quantity': qty, 'price': price})
    return items


def _shipping_methods(items, country, subtotal, coupon_shipping=False):
    """subtotal : après remise du code promo"""
    from routes.cart import _with_free_shipping
    from services.shipping_service import ShippingService
    result = ShippingService().calculate_shipping([{
        'product_id': i['product'].id, 'cj_pid': i['product'].cj_pid,
        'cj_vid': i['variant'].cj_vid if i['variant'] is not None else None,
        'quantity': i['quantity'], 'product': i['product'],
    } for i in items], country)
    return _with_free_shipping(result.get('methods', []), subtotal, country, items, coupon_shipping,
                               _free_shipping_threshold(g.partner_site))


def _promo(data, items, subtotal):
    """Code promo envoyé par le partenaire, évalué comme dans le panier MPS (remise plafonnée sans perte)"""
    from services import coupons
    code = coupons.normalize(data.get('coupon_code'))
    empty = {'code': None, 'label': '', 'discount': 0.0, 'net': subtotal, 'free_shipping': False, 'error': None}
    if not code:
        return empty
    email = str((data.get('customer') or {}).get('email') or data.get('email') or '').strip() or None
    result = coupons.evaluate(coupons.find(code), items, subtotal, email)
    if result['error']:
        return {**empty, 'error': result['error']}
    return {'code': result['code'], 'label': result['label'], 'discount': result['discount'],
            'net': round(subtotal - result['discount'], 2), 'free_shipping': result['free_shipping'], 'error': None}


def _country(data):
    country = (data.get('country') or 'FR').upper()
    if len(country) != 2 or not country.isalpha():
        raise ValueError('Pays invalide')
    return country


@partner_api.route('/shipping', methods=['POST'])
@partner_required
def shipping():
    data = request.get_json(silent=True) or {}
    try:
        items = _items(data.get('items'))
        country = _country(data)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    subtotal = round(sum(i['price'] * i['quantity'] for i in items), 2)
    promo = _promo(data, items, subtotal)
    methods = [{k: m.get(k) for k in ('code', 'name', 'price', 'delivery_time', 'days')}
               for m in _shipping_methods(items, country, promo['net'], promo['free_shipping'])]
    return jsonify({'subtotal': subtotal, 'discount': promo['discount'], 'net': promo['net'], 'methods': methods,
                    'coupon': {k: promo[k] for k in ('code', 'label', 'error')},
                    'free_shipping_threshold': _free_shipping_threshold(g.partner_site)})


@partner_api.route('/orders', methods=['POST'])
@partner_required
def create_order():
    from services import ines_payment

    data = request.get_json(silent=True) or {}
    customer = {k: str((data.get('customer') or {}).get(k) or '').strip()[:200] for k in CUSTOMER_FIELDS}
    missing = [k for k in CUSTOMER_FIELDS if not customer[k]]
    if missing:
        return jsonify({'error': 'Champs manquants : ' + ', '.join(missing)}), 400
    success_url, cancel_url = data.get('success_url') or '', data.get('cancel_url') or ''
    if not (success_url.startswith('https://') or current_app.config.get('TESTING')) or not cancel_url:
        return jsonify({'error': 'Adresses de retour invalides'}), 400
    if not ines_payment.enabled():
        return jsonify({'error': 'Paiement momentanément indisponible'}), 503
    try:
        items = _items(data.get('items'))
        country = _country(data)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    subtotal = round(sum(i['price'] * i['quantity'] for i in items), 2)
    promo = _promo(data, items, subtotal)
    if promo['error']:
        return jsonify({'error': promo['error']}), 409
    method = next((m for m in _shipping_methods(items, country, promo['net'], promo['free_shipping'])
                   if m.get('code') == data.get('shipping_method')), None)
    if method is None:
        return jsonify({'error': "Cette méthode de livraison n'est plus disponible"}), 409
    shipping_cost = round(float(method['price']), 2)
    site = g.partner_site
    try:
        order = Order(
            status='pending', payment_status='pending', payment_method='card',
            subtotal=subtotal, shipping_cost=shipping_cost, tax=0, total_price=round(promo['net'] + shipping_cost, 2),
            discount_amount=promo['discount'], coupon_code=promo['code'],
            customer_email=customer['email'].lower(), customer_phone=customer['phone'],
            shipping_first_name=customer['first_name'], shipping_last_name=customer['last_name'],
            shipping_address=customer['address'], shipping_city=customer['city'],
            shipping_postal_code=customer['postal_code'], shipping_country=country,
            shipping_method=method.get('code'), customer_notes=(data.get('notes') or '')[:2000] or None,
            admin_notes=f"Commande passée sur {SITE_LABELS.get(site, site)}",
        )
        db.session.add(order)
        db.session.flush()
        for i in items:
            db.session.add(OrderItem(order_id=order.id, product_id=i['product'].id,
                                     variant_id=i['variant'].id if i['variant'] is not None else None,
                                     quantity=i['quantity'], price=i['price']))
        db.session.commit()
        session = ines_payment.create_checkout(order, success_url=success_url, cancel_url=cancel_url)
    except ines_payment.PaymentError as e:
        current_app.logger.error("Session de paiement partenaire (%s) non créée : %s", site, e)
        return jsonify({'error': "Le paiement n'a pas pu démarrer"}), 502
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Commande partenaire (%s) non créée", site)
        return jsonify({'error': "Commande non enregistrée"}), 500
    return jsonify({'order_number': order.order_number, 'total': order.total_price,
                    'shipping_cost': shipping_cost, 'checkout_url': session['url']}), 201


def _order_json(order):
    return {
        'order_number': order.order_number, 'status': order.status, 'payment_status': order.payment_status,
        'total': order.total_price, 'shipping_cost': order.shipping_cost,
        'created_at': order.created_at.isoformat() if order.created_at else None,
        'tracking_number': order.cj_tracking_number, 'carrier': order.cj_logistics_name,
        'items': [{'name': it.product.name if it.product else '', 'quantity': it.quantity, 'price': it.price,
                   'image_url': it.product.image_url if it.product else None,
                   'options': ' / '.join(x for x in (it.variant.color, it.variant.size) if x) if it.variant else ''}
                  for it in order.order_items],
    }


def _partner_order(site, **filters):
    label = f"Commande passée sur {SITE_LABELS.get(site, site)}"
    return Order.query.filter_by(admin_notes=label, **filters)


@partner_api.route('/orders/confirm', methods=['POST'])
@partner_required
def confirm_order():
    from services import ines_payment

    session_id = ((request.get_json(silent=True) or {}).get('session_id') or '')[:255]
    order = _partner_order(g.partner_site, stripe_session_id=session_id).first() if session_id else None
    if not order:
        return jsonify({'error': 'Commande introuvable'}), 404
    if order.payment_status != 'paid':
        try:
            ines_payment.fulfill(order.id, ines_payment.get_session(session_id))
        except ines_payment.PaymentError as e:
            current_app.logger.error("Vérification du paiement partenaire impossible (%s) : %s", session_id, e)
            return jsonify({'error': 'Vérification du paiement impossible', 'retry': True}), 502
        order = Order.query.get(order.id)
    return jsonify(_order_json(order))


@partner_api.route('/orders')
@partner_required
def list_orders():
    email = (request.args.get('email') or '').strip().lower()
    if '@' not in email:
        return jsonify({'error': 'E-mail requis'}), 400
    orders = (_partner_order(g.partner_site, customer_email=email)
              .filter(Order.payment_status != 'pending').order_by(Order.created_at.desc()).limit(50).all())
    return jsonify({'orders': [_order_json(o) for o in orders]})


@partner_api.route('/newsletter', methods=['POST'])
@partner_required
def newsletter():
    """Inscription depuis une vitrine : même liste et même code -10 % que MPS, source = le site.
    L'e-mail de bienvenue porte le nom et l'adresse de la vitrine ; le code s'utilise sur la vitrine."""
    from services import newsletter as nl
    data = request.get_json(silent=True) or {}
    if not data.get('consent'):
        return jsonify({'error': "Cochez la case pour accepter de recevoir nos e-mails."}), 400
    try:
        sub, coupon, created = nl.subscribe(data.get('email'), source=g.partner_site[:40])
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    shop_url = str(data.get('site_url') or '')
    shop_url = shop_url[:200] if shop_url.startswith('https://') else None
    nl.send_welcome(sub, coupon, current_app.config['SITE_URL'],
                    shop_name=str(data.get('site_name') or SITE_LABELS.get(g.partner_site, g.partner_site))[:60],
                    shop_url=shop_url)
    return jsonify({'created': created, 'code': coupon.code, 'discount': int(coupon.value),
                    'min_subtotal': coupon.min_subtotal}), 201 if created else 200


@partner_api.route('/stats')
@partner_required
def stats():
    """Chiffres de la boutique pour les moniteurs d'INES (jeton PARTNER_TOKEN_INES), en lecture seule."""
    if g.partner_site != 'ines':
        return jsonify({'error': 'Réservé à INES'}), 403
    from datetime import datetime, timedelta
    now = datetime.utcnow()
    paid = Order.query.filter(Order.payment_status == 'paid')

    def period(days):
        orders = paid.filter(Order.paid_at >= now - timedelta(days=days)).all()
        margins = [m for m in (o.product_margin() for o in orders) if m is not None]
        return {'orders': len(orders), 'revenue': round(sum(o.total_price or 0 for o in orders), 2),
                'margin': round(sum(margins), 2), 'margin_unknown': len(orders) - len(margins)}

    sites = {'multiproshop': paid.filter(~Order.admin_notes.like('Commande passée sur %') | Order.admin_notes.is_(None)).count()}
    for site in set(_partners()) - {'ines'}:
        sites[site] = _partner_order(site).filter(Order.payment_status == 'paid').count()
    online = _visible()
    last_sync = db.session.query(db.func.max(Product.cj_last_sync)).scalar()
    return jsonify({
        'generated_at': now.isoformat() + 'Z',
        'sales': {'today': period(1), 'week': period(7), 'month': period(30)},
        'paid_orders_by_site': sites,
        # payées mais pas encore passées chez CJ : à surveiller (paiement reçu, rien d'envoyé)
        'to_send_to_cj': paid.filter(Order.cj_order_id.is_(None), Order.status.notin_(['cancelled', 'delivered'])).count(),
        'shipped_in_transit': Order.query.filter(Order.status == 'shipped').count(),
        'products_online': online.count(),
        'products_out_of_stock': online.filter(db.func.coalesce(Product.stock, 0) <= 0).count(),
        'last_cj_sync': last_sync.isoformat() + 'Z' if last_sync else None,
    })
