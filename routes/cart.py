from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, current_app
from flask_login import login_required, current_user
from models.cart import Cart
from models.product import Product

cart_bp = Blueprint('cart', __name__, url_prefix='/cart')

@cart_bp.route('/')
def view_cart():
    """Afficher le panier"""
    from flask import session
    
    from services.product_service import ProductService

    cart = Cart()
    items = cart.get_items_with_products()
    total = cart.get_total_price()
    suggestions = ProductService.get_cart_suggestions([item['product'] for item in items])
    
    return render_template('pages/cart.html',
                         cart_items=items,
                         total=total,
                         cart=cart,
                         suggestions=suggestions)

def _wants_json():
    """Appel AJAX (fiche produit, cart.js) ou simple formulaire HTML (cartes produits)."""
    return request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest' \
        or request.accept_mimetypes.best == 'application/json'


def _with_free_shipping(methods, subtotal, country):
    """Livraison offerte en France dès le seuil affiché sur le site : la méthode la moins chère passe à 0 €."""
    if not methods or country not in current_app.config['FREE_SHIPPING_COUNTRIES'] \
            or subtotal < current_app.config['FREE_SHIPPING_THRESHOLD']:
        return methods
    methods = [dict(m) for m in methods]
    cheapest = min(methods, key=lambda m: m['price'])
    cheapest['price'] = 0
    return sorted(methods, key=lambda m: m['price'])


@cart_bp.route('/add', methods=['POST'])
def add_to_cart():
    """Ajouter un produit au panier avec variante optionnelle (AJAX)"""
    try:
        from models.product_variant import ProductVariant
        
        data = request.get_json() if request.is_json else request.form
        product_id = int(data.get('product_id'))
        quantity = int(data.get('quantity', 1))
        variant_id = data.get('variant_id')
        
        if variant_id:
            variant_id = int(variant_id)
        
        # Vérifier que le produit existe
        product = Product.query.get(product_id)
        if not product:
            return jsonify({
                'success': False,
                'message': 'Produit introuvable'
            }), 404
        
        # Si variante, vérifier son stock
        if variant_id:
            variant = ProductVariant.query.get(variant_id)
            if not variant:
                return jsonify({
                    'success': False,
                    'message': 'Variante introuvable'
                }), 404
            
            if not variant.active:
                return jsonify({
                    'success': False,
                    'message': 'Cette variante n\'est plus disponible'
                }), 400
            
            if variant.stock < quantity:
                return jsonify({
                    'success': False,
                    'message': f'Stock insuffisant. Seulement {variant.stock} disponible(s)'
                }), 400
            
            message = f'{product.name} ({variant.display_name}) ajouté au panier'
        else:
            if product.variants.count():
                # Taille, couleur… : le choix se fait sur la fiche produit
                message = 'Choisissez une option (taille, couleur…) sur la fiche du produit'
                url = url_for('products.product_detail', product_id=product.id)
                if not _wants_json():
                    flash(message, 'info')
                    return redirect(url)
                return jsonify({'success': False, 'needs_variant': True, 'url': url, 'message': message}), 400

            # Vérifier le stock du produit
            if product.stock < quantity:
                return jsonify({
                    'success': False,
                    'message': f'Stock insuffisant. Seulement {product.stock} disponible(s)'
                }), 400
            
            message = f'{product.name} ajouté au panier'
        
        # Ajouter au panier
        cart = Cart()
        cart.add_item(product_id, quantity, variant_id)

        if not _wants_json():
            flash(message, 'success')
            return redirect(request.referrer or url_for('cart.view_cart'))

        return jsonify({
            'success': True,
            'message': message,
            'cart_total': cart.get_total_items(),
            'cart_count': cart.get_item_count()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@cart_bp.route('/update/<cart_key>', methods=['POST'])
def update_quantity(cart_key):
    """Mettre à jour la quantité d'un produit (AJAX)"""
    try:
        data = request.get_json() if request.is_json else request.form
        quantity = int(data.get('quantity', 1))
        
        # Extraire le product_id depuis la cart_key
        product_id = int(cart_key.split('_')[0])
        product = Product.query.get(product_id)
        if not product:
            return jsonify({
                'success': False,
                'message': 'Produit introuvable'
            }), 404
        
        # Vérifier le stock
        if quantity > 0 and product.stock < quantity:
            return jsonify({
                'success': False,
                'message': f'Stock insuffisant. Seulement {product.stock} disponible(s)'
            }), 400
        
        # Mettre à jour
        cart = Cart()
        cart.update_quantity(cart_key, quantity)
        
        # Recalculer le total
        items = cart.get_items_with_products()
        subtotal = next((item['subtotal'] for item in items if item['cart_key'] == cart_key), 0)
        
        return jsonify({
            'success': True,
            'message': 'Quantité mise à jour',
            'cart_total': cart.get_total_items(),
            'cart_count': cart.get_item_count(),
            'total_price': cart.get_total_price(),
            'item_subtotal': subtotal
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@cart_bp.route('/remove/<cart_key>', methods=['POST'])
def remove_from_cart(cart_key):
    """Supprimer un produit du panier (AJAX)"""
    try:
        cart = Cart()
        
        if cart.remove_item(cart_key):
            return jsonify({
                'success': True,
                'message': 'Produit retiré du panier',
                'cart_total': cart.get_total_items(),
                'cart_count': cart.get_item_count(),
                'total_price': cart.get_total_price()
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Produit non trouvé dans le panier'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@cart_bp.route('/clear', methods=['POST'])
def clear_cart():
    """Vider le panier"""
    cart = Cart()
    cart.clear()
    
    if request.is_json:
        return jsonify({
            'success': True,
            'message': 'Panier vidé'
        })
    else:
        flash('Panier vidé', 'success')
        return redirect(url_for('cart.view_cart'))

@cart_bp.route('/count')
def cart_count():
    """Obtenir le nombre d'articles dans le panier (AJAX)"""
    cart = Cart()
    return jsonify({
        'total_items': cart.get_total_items(),
        'item_count': cart.get_item_count()
    })

@cart_bp.route('/shipping-methods', methods=['POST'])
def get_checkout_shipping():
    """Calculer les méthodes de livraison CJ pour le panier en session"""
    try:
        data = request.get_json() or {}
        country_code = data.get('country', 'FR')
        
        cart = Cart()
        items = cart.get_items_with_products()
        
        if not items:
            return jsonify({'success': False, 'methods': [], 'message': 'Panier vide'}), 400
        
        # Préparer les items pour le ShippingService
        shipping_items = []
        for item in items:
            product = item['product']
            shipping_items.append({
                'product_id': product.id,
                'cj_pid': product.cj_pid,
                'cj_vid': item['variant'].cj_vid if item['variant'] is not None else None,
                'quantity': item['quantity'],
                'product': product
            })
        
        from services.shipping_service import ShippingService
        shipping_service = ShippingService()
        result = shipping_service.calculate_shipping(shipping_items, country_code)
        result['methods'] = _with_free_shipping(result.get('methods', []), cart.get_total_price(), country_code)

        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'methods': [],
            'message': str(e)
        }), 500

# Micro-entreprise en franchise de TVA (art. 293 B du CGI) : aucune TVA facturée
REQUIRED_FIELDS = {
    'first_name': 'prénom', 'last_name': 'nom', 'email': 'e-mail', 'phone': 'téléphone',
    'address': 'adresse', 'city': 'ville', 'postal_code': 'code postal',
}


def _shipping_price(items, country, method_code, subtotal):
    """Prix de la méthode de livraison choisie, recalculé ici (jamais celui envoyé par le navigateur)."""
    from services.shipping_service import ShippingService
    shipping_items = [{
        'product_id': item['product'].id,
        'cj_pid': item['product'].cj_pid,
        'cj_vid': item['variant'].cj_vid if item['variant'] is not None else None,
        'quantity': item['quantity'],
        'product': item['product'],
    } for item in items]
    result = ShippingService().calculate_shipping(shipping_items, country)
    for method in _with_free_shipping(result.get('methods', []), subtotal, country):
        if method.get('code') == method_code:
            return round(float(method['price']), 2)
    return None


def _remember_order(order_id):
    """Un invité ne peut voir que les commandes passées depuis son navigateur."""
    ids = session.get('my_orders', [])
    if order_id not in ids:
        session['my_orders'] = (ids + [order_id])[-20:]


@cart_bp.route('/remember-email', methods=['POST'])
def remember_email():
    """E-mail saisi au paiement : garde le panier pour les relances (1 h, 24 h, 72 h)"""
    from services import cart_reminders

    data = request.get_json(silent=True) or {}
    token = cart_reminders.remember(data.get('email'), session.get('cart'), session.get('reminder_token'))
    if token:
        session['reminder_token'] = token
    return ('', 204)


@cart_bp.route('/reprendre/<token>')
def restore_cart(token):
    """Lien des e-mails de relance : remet le panier enregistré dans ce navigateur"""
    from models.cart_reminder import CartReminder

    reminder = CartReminder.query.filter_by(token=token).first()
    if not reminder:
        flash("Ce lien n'est plus valable.", 'info')
        return redirect(url_for('cart.view_cart'))
    cart = Cart()
    for cart_key, item in reminder.get_items().items():
        if isinstance(item, dict) and cart_key not in cart.get_items():
            product = Product.query.get(item['product_id'])
            if product and product.is_active and product.stock > 0:
                cart.add_item(product.id, item['quantity'], item.get('variant_id'))
    session['reminder_token'] = token
    return redirect(url_for('cart.checkout'))


@cart_bp.route('/relances/stop/<token>')
def stop_reminders(token):
    """Lien de désinscription des relances de panier"""
    from services import cart_reminders

    cart_reminders.stop(token)
    flash("C'est noté : vous ne recevrez plus de rappel pour ce panier.", 'success')
    return redirect(url_for('main.index'))


@cart_bp.route('/checkout', methods=['GET', 'POST'])
def checkout():
    """Page de commande : adresse et livraison, puis paiement sur la page sécurisée Stripe."""
    from services import ines_payment

    cart = Cart()
    items = cart.get_items_with_products()

    if cart.is_empty():
        flash('Votre panier est vide', 'warning')
        return redirect(url_for('products.list_products'))

    stock_errors = cart.validate_stock()
    if stock_errors:
        for error in stock_errors:
            flash(error, 'error')
        return redirect(url_for('cart.view_cart'))

    total = cart.get_total_price()

    if request.method == 'POST':
        from models.order import Order, OrderItem
        from extensions import db

        form = {k: (request.form.get(k) or '').strip() for k in list(REQUIRED_FIELDS) + ['country', 'notes', 'shipping_method']}
        missing = [label for field, label in REQUIRED_FIELDS.items() if not form[field]]
        if missing:
            flash('Champs manquants : ' + ', '.join(missing), 'error')
            return redirect(url_for('cart.checkout'))
        if not form['shipping_method']:
            flash('Veuillez sélectionner une méthode de livraison', 'error')
            return redirect(url_for('cart.checkout'))
        if not ines_payment.enabled():
            current_app.logger.error("Paiement indisponible : INES_API_KEY absente")
            flash('Le paiement est momentanément indisponible. Merci de réessayer dans quelques minutes.', 'error')
            return redirect(url_for('cart.checkout'))

        country = form['country'] or 'FR'
        shipping_cost = _shipping_price(items, country, form['shipping_method'], total)
        if shipping_cost is None:
            flash("Cette méthode de livraison n'est plus disponible, merci d'en choisir une autre.", 'error')
            return redirect(url_for('cart.checkout'))

        try:
            order = Order(
                user_id=current_user.id if current_user.is_authenticated else None,
                status='pending',
                payment_status='pending',
                payment_method='card',
                subtotal=total,
                shipping_cost=shipping_cost,
                tax=0,
                total_price=round(total + shipping_cost, 2),
                customer_email=form['email'],
                customer_phone=form['phone'],
                shipping_first_name=form['first_name'],
                shipping_last_name=form['last_name'],
                shipping_address=form['address'],
                shipping_city=form['city'],
                shipping_postal_code=form['postal_code'],
                shipping_country=country,
                shipping_method=form['shipping_method'],
                customer_notes=form['notes'],
            )
            db.session.add(order)
            db.session.flush()
            for item in items:
                db.session.add(OrderItem(
                    order_id=order.id,
                    product_id=item['product'].id,
                    variant_id=item['variant'].id if item['variant'] is not None else None,
                    quantity=item['quantity'],
                    price=item['price'],
                ))
            db.session.commit()
            _remember_order(order.id)

            # Le stock et le panier ne bougent qu'une fois le paiement confirmé (fulfill)
            checkout_session = ines_payment.create_checkout(
                order,
                success_url=url_for('cart.payment_success', _external=True),
                cancel_url=url_for('cart.payment_cancel', _external=True),
            )
            return redirect(checkout_session['url'], code=303)
        except ines_payment.PaymentError as e:
            current_app.logger.error("Session de paiement non créée : %s", e)
            flash("Le paiement n'a pas pu démarrer. Merci de réessayer dans quelques minutes.", 'error')
            return redirect(url_for('cart.checkout'))
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Commande non créée")
            flash('Une erreur est survenue, votre commande n\'a pas été enregistrée. Merci de réessayer.', 'error')
            return redirect(url_for('cart.checkout'))

    return render_template('pages/checkout.html', cart_items=items, total=total,
                           payment_enabled=ines_payment.enabled())


@cart_bp.route('/order/<int:order_id>')
def order_confirmation(order_id):
    """Page de confirmation de commande"""
    from models.order import Order

    order = Order.query.get_or_404(order_id)

    if current_user.is_authenticated and (order.user_id == current_user.id or current_user.role == 'admin'):
        allowed = True
    else:
        allowed = order_id in session.get('my_orders', [])
    if not allowed:
        flash('Accès non autorisé', 'error')
        return redirect(url_for('main.index'))

    return render_template('pages/order_confirmation.html', order=order)

# ============================================================================
# RETOUR DU PAIEMENT (Stripe d'INES)
# ============================================================================

@cart_bp.route('/payment-success')
def payment_success():
    """Retour de la page de paiement : la commande est validée si Stripe confirme le paiement."""
    from models.order import Order
    from services import ines_payment

    session_id = request.args.get('session_id', '')
    order = Order.query.filter_by(stripe_session_id=session_id).first() if session_id else None
    if not order:
        flash('Session de paiement invalide', 'error')
        return redirect(url_for('cart.view_cart'))

    if order.payment_status != 'paid':
        try:
            stripe_session = ines_payment.get_session(session_id)
        except ines_payment.PaymentError as e:
            current_app.logger.error("Vérification du paiement impossible (%s) : %s", session_id, e)
            flash('Votre paiement est en cours de vérification : vous recevrez un e-mail de confirmation.', 'info')
            return redirect(url_for('main.index'))
        ines_payment.fulfill(order.id, stripe_session)
        db_order = Order.query.get(order.id)
        if db_order.payment_status != 'paid':
            flash("Le paiement n'a pas été confirmé. Vous pouvez réessayer.", 'warning')
            return redirect(url_for('cart.checkout'))

    Cart().clear()
    _remember_order(order.id)
    flash(f'Paiement reçu, merci ! Commande {order.order_number} confirmée.', 'success')
    return redirect(url_for('cart.order_confirmation', order_id=order.id))


@cart_bp.route('/payment-cancel')
def payment_cancel():
    """Paiement abandonné : le panier est conservé."""
    flash('Paiement annulé : votre panier est conservé, vous pouvez réessayer quand vous voulez.', 'info')
    return redirect(url_for('cart.checkout'))
