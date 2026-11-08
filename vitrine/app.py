"""Vitrine d'une niche (Sérénis…) : petite boutique qui affiche les produits MPS d'un projet.

Tout passe par l'API partenaire de MPS (/api/partner) : catalogue du projet, port, commande et
paiement. MPS reste le vendeur (prix, encaissement, commande CJ, e-mails), la vitrine ne garde
que le panier en session. Une autre niche = le même code avec d'autres variables :

  VITRINE_PROJECT  projet MPS (champ « Vitrines » des fiches), ex. serenis
  VITRINE_TOKEN    jeton PARTNER_TOKEN_<PROJET> de MPS
  VITRINE_NAME, VITRINE_TAGLINE, VITRINE_URL (https://serenis.multiproshop.com), VITRINE_COLOR
  MPS_API          http://multiproshop-web:8000/api/partner sur le réseau Docker
  SECRET_KEY       clé de session
Lancement : gunicorn vitrine.app:app (voir deploy/docker-compose.yml).
"""
import os

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
    'color': os.environ.get('VITRINE_COLOR', '#5b6c8f'),
}
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


@app.context_processor
def globals_():
    return {'site': SITE, 'cart_count': sum(line['quantity'] for line in session.get('cart', []))}


@app.errorhandler(ApiError)
def api_error(e):
    return render_template('error.html', message=str(e)), 503


@app.route('/')
def index():
    params = {'project': PROJECT, 'per_page': 60, 'page': request.args.get('page', 1)}
    for key in ('category', 'q', 'sort'):
        if request.args.get(key):
            params[key] = request.args[key]
    return render_template('index.html', data=api('GET', '/catalogue', params=params), args=request.args)


@app.route('/produit/<int:product_id>')
def product(product_id):
    try:
        p = api('GET', f'/products/{product_id}', params={'project': PROJECT})
    except ApiError:
        abort(404)
    return render_template('product.html', p=p)


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
    return render_template('cart.html', lines=lines, subtotal=round(sum(x['total'] for x in lines), 2))


@app.route('/panier/ajouter', methods=['POST'])
def cart_add():
    try:
        pid = int(request.form['product_id'])
        vid = int(request.form['variant_id']) if request.form.get('variant_id') else None
        qty = max(1, min(20, int(request.form.get('quantity', 1))))
    except (KeyError, ValueError):
        abort(400)
    cart = session.get('cart', [])
    for line in cart:
        if line['product_id'] == pid and line.get('variant_id') == vid:
            line['quantity'] = min(20, line['quantity'] + qty)
            break
    else:
        cart.append({'product_id': pid, 'variant_id': vid, 'quantity': qty})
    session['cart'] = cart[:30]
    flash('Ajouté au panier')
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
    shipping = api('POST', '/shipping', json={'items': _items(), 'country': form['country']})
    if request.method == 'POST' and request.form.get('step') == 'pay':
        missing = [k for k in CUSTOMER if not form[k]]
        if missing or not form['shipping_method']:
            flash('Merci de remplir tous les champs et de choisir une livraison.')
        else:
            try:
                order = api('POST', '/orders', json={
                    'items': _items(), 'country': form['country'], 'shipping_method': form['shipping_method'],
                    'customer': {k: form[k] for k in CUSTOMER}, 'notes': form['notes'],
                    'success_url': SITE['url'] + '/merci?session_id={CHECKOUT_SESSION_ID}',
                    'cancel_url': SITE['url'] + '/panier'})
            except ApiError as e:
                flash(str(e))
            else:
                return redirect(order['checkout_url'], code=303)
    return render_template('checkout.html', form=form, shipping=shipping, countries=COUNTRIES)


@app.route('/merci')
def thanks():
    session_id = request.args.get('session_id', '')
    try:
        order = api('POST', '/orders/confirm', json={'session_id': session_id}) if session_id else None
    except ApiError as e:
        return render_template('error.html', message=str(e)), 502
    if order and order.get('payment_status') == 'paid':
        session.pop('cart', None)
    return render_template('thanks.html', order=order)


@app.route('/health')
def health():
    return {'ok': True}
