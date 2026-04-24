from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models.cart import Cart
from models.product import Product

cart_bp = Blueprint('cart', __name__, url_prefix='/cart')

@cart_bp.route('/')
def view_cart():
    """Afficher le panier"""
    from flask import session
    
    cart = Cart()
    items = cart.get_items_with_products()
    total = cart.get_total_price()
    
    return render_template('pages/cart.html',
                         cart_items=items,
                         total=total,
                         cart=cart)

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
                'cj_vid': item.get('variant_cj_vid'),
                'quantity': item['quantity'],
                'product': product
            })
        
        from services.shipping_service import ShippingService
        shipping_service = ShippingService()
        result = shipping_service.calculate_shipping(shipping_items, country_code)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'methods': [],
            'message': str(e)
        }), 500

@cart_bp.route('/checkout', methods=['GET', 'POST'])
def checkout():
    """Page de checkout"""
    cart = Cart()
    items = cart.get_items_with_products()
    
    # Vérifier que le panier n'est pas vide
    if cart.is_empty():
        flash('Votre panier est vide', 'warning')
        return redirect(url_for('products.list_products'))
    
    # Valider le stock
    stock_errors = cart.validate_stock()
    if stock_errors:
        for error in stock_errors:
            flash(error, 'error')
        return redirect(url_for('cart.view_cart'))
    
    total = cart.get_total_price()
    
    if request.method == 'POST':
        try:
            from models.order import Order, OrderItem
            from extensions import db
            
            # Récupérer les données du formulaire
            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')
            email = request.form.get('email')
            phone = request.form.get('phone')
            address = request.form.get('address')
            city = request.form.get('city')
            postal_code = request.form.get('postal_code')
            country = request.form.get('country', 'FR')
            notes = request.form.get('notes', '')
            
            # Récupérer les frais de livraison depuis le formulaire
            shipping_method = request.form.get('shipping_method', '').strip()
            if not shipping_method:
                flash('Veuillez sélectionner une méthode de livraison', 'error')
                return redirect(url_for('cart.checkout'))
            
            try:
                shipping_cost = float(request.form.get('shipping_cost', 0))
            except (ValueError, TypeError):
                shipping_cost = 0
            
            tax = total * 0.2  # TVA 20%
            total_with_tax = total + shipping_cost + tax
            
            # Créer la commande
            order = Order(
                user_id=current_user.id if current_user.is_authenticated else None,
                status='pending',
                payment_status='pending',
                payment_method='card',  # Par défaut
                subtotal=total,
                shipping_cost=shipping_cost,
                tax=tax,
                total_price=total_with_tax,
                customer_email=email,
                customer_phone=phone,
                shipping_first_name=first_name,
                shipping_last_name=last_name,
                shipping_address=address,
                shipping_city=city,
                shipping_postal_code=postal_code,
                shipping_country=country,
                shipping_method=shipping_method,
                customer_notes=notes
            )
            
            db.session.add(order)
            db.session.flush()  # Pour obtenir l'ID de la commande
            
            # Créer les items de commande
            for item in items:
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=item['product'].id,
                    variant_id=item.get('variant_id'),  # Support des variantes
                    quantity=item['quantity'],
                    price=item['product'].price
                )
                db.session.add(order_item)
                
                # Réduire le stock (variante ou produit)
                if item.get('variant_id'):
                    from models.product_variant import ProductVariant
                    variant = ProductVariant.query.get(item['variant_id'])
                    if variant:
                        variant.stock -= item['quantity']
                else:
                    item['product'].reduce_stock(item['quantity'])
            
            db.session.commit()
            
            # Envoyer l'email de confirmation
            try:
                from utils.email import send_order_confirmation_email
                send_order_confirmation_email(order)
            except Exception as e:
                print(f"Erreur envoi email: {e}")
            
            # Vider le panier
            cart.clear()
            
            flash(f'Commande {order.order_number} créée avec succès !', 'success')
            return redirect(url_for('cart.order_confirmation', order_id=order.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la création de la commande: {str(e)}', 'error')
            return redirect(url_for('cart.checkout'))
    
    return render_template('pages/checkout.html', cart_items=items, total=total)

@cart_bp.route('/order/<int:order_id>')
def order_confirmation(order_id):
    """Page de confirmation de commande"""
    from models.order import Order
    
    order = Order.query.get_or_404(order_id)
    
    # Vérifier que l'utilisateur peut voir cette commande
    if current_user.is_authenticated:
        if order.user_id != current_user.id and not current_user.role == 'admin':
            flash('Accès non autorisé', 'error')
            return redirect(url_for('main.index'))
    
    return render_template('pages/order_confirmation.html', order=order)

# ============================================================================
# ROUTES STRIPE PAYMENT
# ============================================================================

@cart_bp.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    """Créer une session de paiement Stripe"""
    import stripe
    from flask import current_app
    
    stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
    
    try:
        cart = Cart()
        items = cart.get_items_with_products()
        
        if cart.is_empty():
            return jsonify({'error': 'Panier vide'}), 400
        
        # Créer les line items pour Stripe
        line_items = []
        for item in items:
            line_items.append({
                'price_data': {
                    'currency': 'eur',
                    'product_data': {
                        'name': item['product'].name,
                        'images': [item['product'].image_url] if item['product'].image_url else [],
                    },
                    'unit_amount': int(item['product'].price * 100),  # Stripe utilise les centimes
                },
                'quantity': item['quantity'],
            })
        
        # Créer la session Stripe
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=request.host_url + 'cart/payment-success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.host_url + 'cart/payment-cancel',
            metadata={
                'user_id': current_user.id if current_user.is_authenticated else None,
            }
        )
        
        return jsonify({'id': checkout_session.id})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 403

@cart_bp.route('/payment-success')
def payment_success():
    """Page de succès après paiement Stripe"""
    import stripe
    from flask import current_app
    
    stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
    session_id = request.args.get('session_id')
    
    if not session_id:
        flash('Session de paiement invalide', 'error')
        return redirect(url_for('cart.view_cart'))
    
    try:
        # Récupérer la session Stripe
        session = stripe.checkout.Session.retrieve(session_id)
        
        # Créer la commande si le paiement est réussi
        if session.payment_status == 'paid':
            from models.order import Order, OrderItem
            from extensions import db
            from datetime import datetime
            
            cart = Cart()
            items = cart.get_items_with_products()
            
            # Calculer les totaux
            subtotal = sum(item['subtotal'] for item in items)
            shipping_cost = 5.99 if subtotal < 50 else 0
            tax = (subtotal + shipping_cost) * 0.20
            total = subtotal + shipping_cost + tax
            
            # Créer la commande
            order = Order(
                user_id=current_user.id if current_user.is_authenticated else None,
                order_number=f"CMD-{datetime.now().strftime('%Y%m%d')}-{Order.query.count() + 1:04d}",
                customer_email=session.customer_details.email if session.customer_details else '',
                customer_phone='',
                shipping_first_name=session.customer_details.name.split()[0] if session.customer_details and session.customer_details.name else '',
                shipping_last_name=' '.join(session.customer_details.name.split()[1:]) if session.customer_details and session.customer_details.name else '',
                shipping_address='',
                shipping_city='',
                shipping_postal_code='',
                shipping_country='FR',
                subtotal=subtotal,
                shipping_cost=shipping_cost,
                tax=tax,
                total_price=total,
                payment_method='card',
                payment_status='paid',
                status='paid',
                stripe_session_id=session_id,
                paid_at=datetime.utcnow()
            )
            
            db.session.add(order)
            db.session.flush()
            
            # Ajouter les items
            for item in items:
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=item['product'].id,
                    variant_id=item.get('variant_id'),  # Support des variantes
                    quantity=item['quantity'],
                    price=item['product'].price
                )
                db.session.add(order_item)
                
                # Décrémenter le stock (variante ou produit)
                if item.get('variant_id'):
                    from models.product_variant import ProductVariant
                    variant = ProductVariant.query.get(item['variant_id'])
                    if variant:
                        variant.stock -= item['quantity']
                else:
                    item['product'].stock -= item['quantity']
            
            db.session.commit()
            
            # Créer la commande sur CJ Dropshipping automatiquement
            try:
                from models.api_provider import ApiProvider
                from services.api_providers.cj_dropshipping_optimized import CJDropshippingProvider
                from services.cj_order_service import CjOrderService
                
                provider = ApiProvider.query.filter_by(name='CJ Dropshipping', active=True).first()
                if provider:
                    cj_api = CJDropshippingProvider(provider)
                    cj_service = CjOrderService(cj_api)
                    
                    # Créer la commande sur CJ
                    cj_result = cj_service.create_cj_order(order.id)
                    
                    if cj_result.get('success'):
                        print(f"✅ Commande CJ créée: {cj_result.get('cj_order_id')}")
                    else:
                        print(f"⚠️ Erreur création commande CJ: {cj_result.get('message')}")
                        # Ne pas bloquer la commande si CJ échoue
            except Exception as e:
                print(f"⚠️ Exception lors de la création commande CJ: {e}")
                # Ne pas bloquer la commande
            
            cart.clear()
            
            flash(f'Paiement réussi ! Commande {order.order_number} créée.', 'success')
            return redirect(url_for('cart.order_confirmation', order_id=order.id))
        else:
            flash('Le paiement n\'a pas été complété', 'warning')
            return redirect(url_for('cart.checkout'))
            
    except Exception as e:
        flash(f'Erreur lors de la vérification du paiement: {str(e)}', 'error')
        return redirect(url_for('cart.checkout'))

@cart_bp.route('/payment-cancel')
def payment_cancel():
    """Page d'annulation de paiement"""
    flash('Paiement annulé. Vous pouvez réessayer quand vous voulez.', 'info')
    return redirect(url_for('cart.checkout'))

@cart_bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    """Webhook Stripe pour les événements de paiement"""
    import stripe
    from flask import current_app
    
    stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
    endpoint_secret = current_app.config['STRIPE_WEBHOOK_SECRET']
    
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError:
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError:
        return jsonify({'error': 'Invalid signature'}), 400
    
    # Gérer les événements
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        # Traiter la commande (déjà fait dans payment_success)
        print(f"✅ Paiement complété: {session['id']}")
    
    elif event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        print(f"✅ Payment Intent réussi: {payment_intent['id']}")
    
    return jsonify({'status': 'success'})
