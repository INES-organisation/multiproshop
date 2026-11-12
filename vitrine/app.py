"""Vitrine d'une niche (Sérénis…) : petite boutique qui affiche les produits MPS d'un projet.

Tout passe par l'API partenaire de MPS (/api/partner) : catalogue du projet, port, commande et
paiement. MPS reste le vendeur (prix, encaissement, commande CJ, e-mails), la vitrine ne garde
que le panier en session. Une autre niche = le même code avec d'autres variables :

  VITRINE_PROJECT  projet MPS (champ « Vitrines » des fiches), ex. serenis
  VITRINE_TOKEN    jeton PARTNER_TOKEN_<PROJET> de MPS
  VITRINE_NAME, VITRINE_TAGLINE, VITRINE_URL (https://serenis.multiproshop.com), VITRINE_COLOR
  VITRINE_HERO     id MPS du produit mis en avant en haut de l'accueil (le premier produit sinon)
  VITRINE_RITUALS  lots présentés à l'accueil, en JSON : [{"name", "text", "ids": [id, …]}, …]
  VITRINE_DELIVERY délai de livraison annoncé, en jours, ex. 12-20
  MPS_API          http://multiproshop-web:8000/api/partner sur le réseau Docker
Les réglages saisis dans l'admin MPS › Boutiques et vitrines (/api/partner/storefront/<projet>) passent
avant les VITRINE_* ci-dessus, qui restent la valeur de secours.
  SECRET_KEY       clé de session
Lancement : gunicorn vitrine.app:app (voir deploy/docker-compose.yml).
"""
import json
import os
import time
from datetime import date, timedelta

import requests
from flask import Flask, abort, flash, redirect, render_template, request, session, url_for

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or (os.urandom(32) if os.environ.get('VITRINE_TESTING') else None)
if not app.secret_key:
    raise RuntimeError('SECRET_KEY manquante pour la vitrine')
app.config.update(SESSION_COOKIE_SECURE=not app.debug and not os.environ.get('VITRINE_TESTING'),
                  SESSION_COOKIE_SAMESITE='Lax')
API = os.environ.get('MPS_API', 'http://multiproshop-web:8000/api/partner').rstrip('/')
PROJECT = os.environ.get('VITRINE_PROJECT', 'serenis')
SITE = {
    'name': os.environ.get('VITRINE_NAME', 'Sérénis'),
    'tagline': os.environ.get('VITRINE_TAGLINE', 'Le rituel du soir : sommeil, détente et cocooning'),
    'url': os.environ.get('VITRINE_URL', 'https://serenis.multiproshop.com').rstrip('/'),
    'color': os.environ.get('VITRINE_COLOR', '#e0975a'),
    'hero': os.environ.get('VITRINE_HERO', '20987'),
    'delivery': os.environ.get('VITRINE_DELIVERY', '12-20'),
}
# Lots de l'accueil : produits Sérénis existants, vendus ensemble au prix de chacun (MPS recalcule tout)
DEFAULT_RITUALS = [
    {'name': 'Rituel du soir', 'text': 'Une lumière douce pour se lever, une brume légère et une lueur ambrée pour se coucher.',
     'ids': [20987, 20986, 21135]},
    {'name': 'Nuit étoilée', 'text': "Un ciel étoilé au plafond et une petite flamme pour s'endormir sans le noir complet.",
     'ids': [21093, 20955]},
    {'name': 'Cocon du dimanche', 'text': 'Plaid, coussin et couverture de sieste : tout pour ne plus quitter le canapé.',
     'ids': [20913, 20910, 20911]},
]
try:
    RITUALS = json.loads(os.environ['VITRINE_RITUALS']) if os.environ.get('VITRINE_RITUALS') else DEFAULT_RITUALS
except ValueError:
    RITUALS = DEFAULT_RITUALS
MONTHS = ('janv.', 'févr.', 'mars', 'avr.', 'mai', 'juin', 'juil.', 'août', 'sept.', 'oct.', 'nov.', 'déc.')
COUNTRIES = {'FR': 'France', 'BE': 'Belgique', 'LU': 'Luxembourg', 'CH': 'Suisse', 'RE': 'La Réunion'}
CUSTOMER = ('first_name', 'last_name', 'email', 'phone', 'address', 'city', 'postal_code')


class ApiError(Exception):
    pass


def api(method, path, **kwargs):
    headers = {'Authorization': 'Bearer ' + os.environ.get('VITRINE_TOKEN', '')}
    try:
        r = requests.request(method, API + path, headers=headers, timeout=20, **kwargs)
        data = r.json()
    except (requests.RequestException, ValueError):
        raise ApiError('La boutique est momentanément indisponible, réessayez dans un instant.')
    if r.status_code >= 400:
        raise ApiError(data.get('error') or 'Erreur de la boutique')
    return data


_shop = {'at': 0, 'data': None}


def shop():
    """Catalogue complet de la vitrine (60 produits au plus), relu toutes les 5 minutes : accueil, lots,
    suggestions et seuil de livraison offerte."""
    if _shop['data'] is None or time.time() - _shop['at'] > 300:
        _shop['data'] = api('GET', '/catalogue', params={'project': PROJECT, 'per_page': 60})
        _shop['at'] = time.time()
    return _shop['data']


_settings = {'at': 0}


@app.before_request
def load_settings():
    """Réglages saisis dans l'admin MPS › Boutiques et vitrines (nom, slogan, couleur, produit mis en
    avant, lots, délai), relus toutes les 5 minutes. Les VITRINE_* servent si MPS ne répond pas."""
    global RITUALS
    if time.time() - _settings['at'] < 300:
        return
    _settings['at'] = time.time()
    try:
        data = api('GET', f'/storefront/{PROJECT}')
    except ApiError:
        return
    for key, field in (('name', 'name'), ('tagline', 'tagline'), ('color', 'color'), ('url', 'url'),
                       ('hero', 'hero_product_id'), ('delivery', 'delivery_days')):
        if data.get(field):
            SITE[key] = str(data[field]).rstrip('/') if key == 'url' else str(data[field])
    if data.get('lots'):
        RITUALS = data['lots']


def free_shipping():
    try:
        return (shop().get('free_shipping') or {}).get('threshold')
    except ApiError:
        return None


def rituals(products):
    """Lots dont au moins deux produits sont en ligne, avec leurs produits et leur prix total"""
    by_id = {p['id']: p for p in products}
    result = []
    for index, r in enumerate(RITUALS):
        items = [by_id[i] for i in r.get('ids', []) if i in by_id]
        if len(items) >= 2:
            result.append({**r, 'index': index, 'products': items, 'total': round(sum(p['price_from'] for p in items), 2)})
    return result


def delivery_window(today=None):
    """« entre le 21 nov. et le 29 nov. » d'après VITRINE_DELIVERY"""
    try:
        low, high = (int(x) for x in SITE['delivery'].split('-'))
    except ValueError:
        return None
    today = today or date.today()
    fmt = lambda d: f'{d.day} {MONTHS[d.month - 1]}'
    return f'entre le {fmt(today + timedelta(days=low))} et le {fmt(today + timedelta(days=high))}'


@app.template_filter('eur')
def eur(value):
    return ('%.2f' % (value or 0)).replace('.', ',') + ' €'


@app.context_processor
def globals_():
    return {'site': SITE, 'cart_count': sum(line['quantity'] for line in session.get('cart', [])),
            'free_shipping': free_shipping()}


@app.errorhandler(404)
def not_found(_e):
    return render_template('error.html', message="Cette page n'existe pas ou plus."), 404


@app.errorhandler(ApiError)
def api_error(e):
    return render_template('error.html', message=str(e)), 503


@app.route('/')
def index():
    everything = shop()
    filtered = any(request.args.get(k) for k in ('category', 'q', 'sort', 'prix'))
    data = everything
    if any(request.args.get(k) for k in ('category', 'q', 'sort')):
        params = {'project': PROJECT, 'per_page': 60}
        params.update({k: request.args[k] for k in ('category', 'q', 'sort') if request.args.get(k)})
        data = api('GET', '/catalogue', params=params)
    products = data.get('products', [])
    try:
        max_price = float(request.args['prix']) if request.args.get('prix') else None
    except ValueError:
        max_price = None
    if max_price:
        products = [p for p in products if p['price_from'] <= max_price]
    all_products = everything.get('products', [])
    hero = next((p for p in all_products if str(p['id']) == SITE['hero']), all_products[0] if all_products else None)
    # une photo par collection pour les portes d'entrée
    covers = {}
    for p in all_products:
        covers.setdefault(p.get('category_id'), p.get('image_url'))
    return render_template('index.html', data=data, products=products, args=request.args, hero=hero,
                           rituals=rituals(all_products), covers=covers, filtered=filtered,
                           categories=everything.get('categories', []), delivery=delivery_window())


@app.route('/produit/<int:product_id>')
def product(product_id):
    try:
        p = api('GET', f'/products/{product_id}', params={'project': PROJECT})
    except ApiError:
        abort(404)
    all_products = shop().get('products', [])
    ritual = next((r for r in rituals(all_products) if p['id'] in [x['id'] for x in r['products']]), None)
    related = [x for x in all_products if x['id'] != p['id'] and x.get('category_id') == p.get('category_id')]
    related += [x for x in all_products if x['id'] != p['id'] and x not in related]
    return render_template('product.html', p=p, ritual=ritual, related=related[:4], delivery=delivery_window())


@app.route('/rituel/<int:index>')
def ritual(index):
    """Un lot : chaque produit avec son choix de modèle, ajoutés ensemble au panier"""
    found = next((r for r in rituals(shop().get('products', [])) if r['index'] == index), None)
    if not found:
        abort(404)
    details = []
    for p in found['products']:
        try:
            details.append(api('GET', f"/products/{p['id']}", params={'project': PROJECT}))
        except ApiError:
            continue
    return render_template('ritual.html', ritual=found, details=details, delivery=delivery_window())


def _cart_lines():
    """Panier en session, avec les prix et noms relus chez MPS (jamais ceux du navigateur)."""
    lines = []
    for line in session.get('cart', []):
        try:
            p = api('GET', f"/products/{line['product_id']}", params={'project': PROJECT})
        except ApiError:
            continue
        variant = next((v for v in p.get('variants', []) if v['id'] == line.get('variant_id')), None)
        price = (variant or {}).get('price') or p['price']
        options = ' / '.join(x for x in ((variant or {}).get('color'), (variant or {}).get('size')) if x)
        lines.append({**line, 'name': p['name'], 'image_url': (variant or {}).get('image_url') or p['image_url'],
                      'options': options, 'price': price, 'total': round(price * line['quantity'], 2)})
    return lines


@app.route('/panier')
def cart():
    lines = _cart_lines()
    in_cart = {line['product_id'] for line in lines}
    suggestions = [p for p in shop().get('products', []) if p['id'] not in in_cart and p['price_from'] < 20][:3]
    return render_template('cart.html', lines=lines, subtotal=round(sum(x['total'] for x in lines), 2),
                           suggestions=suggestions)


def _add(cart, pid, vid, qty):
    for line in cart:
        if line['product_id'] == pid and line.get('variant_id') == vid:
            line['quantity'] = min(20, line['quantity'] + qty)
            return
    cart.append({'product_id': pid, 'variant_id': vid, 'quantity': qty})


@app.route('/panier/ajouter', methods=['POST'])
def cart_add():
    try:
        pid = int(request.form['product_id'])
        vid = int(request.form['variant_id']) if request.form.get('variant_id') else None
        qty = max(1, min(20, int(request.form.get('quantity', 1))))
    except (KeyError, ValueError):
        abort(400)
    cart = session.get('cart', [])
    _add(cart, pid, vid, qty)
    session['cart'] = cart[:30]
    flash('Ajouté au panier')
    return redirect(url_for('cart'))


@app.route('/panier/ajouter-rituel', methods=['POST'])
def cart_add_many():
    """Un lot : product_id et variant_id répétés, une ligne par produit"""
    pids, vids = request.form.getlist('product_id'), request.form.getlist('variant_id')
    if not pids or len(pids) != len(vids) or len(pids) > 10:
        abort(400)
    cart = session.get('cart', [])
    try:
        for pid, vid in zip(pids, vids):
            _add(cart, int(pid), int(vid) if vid else None, 1)
    except ValueError:
        abort(400)
    session['cart'] = cart[:30]
    flash('Le rituel est dans votre panier')
    return redirect(url_for('cart'))


@app.route('/panier/quantite/<int:index>', methods=['POST'])
def cart_quantity(index):
    cart = session.get('cart', [])
    try:
        qty = int(request.form.get('quantity', 1))
    except ValueError:
        abort(400)
    if 0 <= index < len(cart):
        if qty <= 0:
            cart.pop(index)
        else:
            cart[index]['quantity'] = min(20, qty)
    session['cart'] = cart
    return redirect(url_for('cart'))


@app.route('/panier/retirer/<int:index>', methods=['POST'])
def cart_remove(index):
    cart = session.get('cart', [])
    if 0 <= index < len(cart):
        cart.pop(index)
    session['cart'] = cart
    return redirect(url_for('cart'))


def _items():
    return [{k: line.get(k) for k in ('product_id', 'variant_id', 'quantity')} for line in session.get('cart', [])]


@app.route('/commande', methods=['GET', 'POST'])
def checkout():
    if not session.get('cart'):
        return redirect(url_for('cart'))
    form = {k: (request.values.get(k) or '').strip() for k in CUSTOMER + ('country', 'shipping_method', 'notes')}
    form['country'] = form['country'] if form['country'] in COUNTRIES else 'FR'
    if 'coupon_code' in request.form:
        session['coupon'] = request.form['coupon_code'].strip().upper()[:40]
    coupon = session.get('coupon') or ''
    shipping = api('POST', '/shipping', json={'items': _items(), 'country': form['country'], 'coupon_code': coupon,
                                              'email': form['email']})
    coupon_error = (shipping.get('coupon') or {}).get('error') if coupon else None
    if coupon_error:  # code gardé (il peut redevenir valable avec un panier plus grand), mais pas appliqué
        shipping = api('POST', '/shipping', json={'items': _items(), 'country': form['country']})
    if request.method == 'POST' and request.form.get('step') == 'pay':
        missing = [k for k in CUSTOMER if not form[k]]
        if missing or not form['shipping_method']:
            flash('Merci de remplir tous les champs et de choisir une livraison.')
        else:
            try:
                order = api('POST', '/orders', json={
                    'items': _items(), 'country': form['country'], 'shipping_method': form['shipping_method'],
                    'customer': {k: form[k] for k in CUSTOMER}, 'notes': form['notes'], 'coupon_code': '' if coupon_error else coupon,
                    'success_url': SITE['url'] + '/merci?session_id={CHECKOUT_SESSION_ID}',
                    'cancel_url': SITE['url'] + '/panier'})
            except ApiError as e:
                flash(str(e))
            else:
                return redirect(order['checkout_url'], code=303)
    return render_template('checkout.html', form=form, shipping=shipping, countries=COUNTRIES, coupon=coupon, coupon_error=coupon_error,
                           lines=_cart_lines(), delivery=delivery_window())


@app.route('/merci')
def thanks():
    session_id = request.args.get('session_id', '')
    try:
        order = api('POST', '/orders/confirm', json={'session_id': session_id}) if session_id else None
    except ApiError as e:
        return render_template('error.html', message=str(e)), 502
    if order and order.get('payment_status') == 'paid':
        session.pop('cart', None)
        session.pop('coupon', None)
    return render_template('thanks.html', order=order)


@app.route('/newsletter', methods=['POST'])
def newsletter():
    if request.form.get('website'):  # champ caché anti-robot
        return redirect(url_for('index'))
    try:
        r = api('POST', '/newsletter', json={'email': request.form.get('email'), 'consent': bool(request.form.get('consent')),
                                             'site_name': SITE['name'], 'site_url': SITE['url']})
    except ApiError as e:
        flash(str(e))
    else:
        session['coupon'] = r['code']
        flash(f"Bienvenue ! Votre code -{r['discount']} % ({r['code']}) vient de vous être envoyé par e-mail. "
              "Il est déjà enregistré pour votre première commande.")
    return redirect(url_for('index') + '#newsletter')


@app.route('/health')
def health():
    return {'ok': True}
