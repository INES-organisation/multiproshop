from extensions import db
from datetime import datetime
import secrets

class Order(db.Model):
    """Modèle de commande"""
    __tablename__ = 'order'
    
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(20), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Nullable pour invités
    
    # Statut et paiement
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, paid, processing, shipped, delivered, cancelled
    payment_status = db.Column(db.String(20), nullable=False, default='pending')  # pending, paid, failed, refunded
    payment_method = db.Column(db.String(50), nullable=True)  # card, paypal, bank_transfer
    stripe_session_id = db.Column(db.String(255), nullable=True)  # ID de session Stripe
    
    # Prix
    subtotal = db.Column(db.Float, nullable=False, default=0.0)
    shipping_cost = db.Column(db.Float, nullable=False, default=0.0)
    tax = db.Column(db.Float, nullable=False, default=0.0)
    total_price = db.Column(db.Float, nullable=False, default=0.0)
    
    # Informations client
    customer_email = db.Column(db.String(120), nullable=False)
    customer_phone = db.Column(db.String(20), nullable=True)
    
    # Adresse de livraison
    shipping_first_name = db.Column(db.String(50), nullable=False)
    shipping_last_name = db.Column(db.String(50), nullable=False)
    shipping_address = db.Column(db.String(200), nullable=False)
    shipping_city = db.Column(db.String(100), nullable=False)
    shipping_postal_code = db.Column(db.String(20), nullable=False)
    shipping_country = db.Column(db.String(2), nullable=False, default='FR')
    
    # Méthode de livraison
    shipping_method = db.Column(db.String(50), nullable=True)  # standard, express
    
    # Notes
    customer_notes = db.Column(db.Text, nullable=True)
    admin_notes = db.Column(db.Text, nullable=True)
    
    # Intégration CJ Dropshipping
    cj_order_id = db.Column(db.String(100), nullable=True)  # ID de la commande sur CJ
    cj_tracking_number = db.Column(db.String(100), nullable=True)  # Numéro de suivi CJ
    cj_status = db.Column(db.String(50), nullable=True)  # Statut CJ
    cj_logistics_name = db.Column(db.String(100), nullable=True)  # Nom du transporteur
    
    # Dates
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    paid_at = db.Column(db.DateTime, nullable=True)
    shipped_at = db.Column(db.DateTime, nullable=True)
    delivered_at = db.Column(db.DateTime, nullable=True)
    
    # Relations
    user = db.relationship('User', backref='orders')
    order_items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')

    def __init__(self, **kwargs):
        super(Order, self).__init__(**kwargs)
        if not self.order_number:
            self.order_number = self.generate_order_number()
    
    @staticmethod
    def generate_order_number():
        """Générer un numéro de commande unique"""
        timestamp = datetime.utcnow().strftime('%Y%m%d')
        random_part = secrets.token_hex(4).upper()
        return f"ORD-{timestamp}-{random_part}"
    
    def get_status_badge(self):
        """Retourner le badge HTML du statut"""
        badges = {
            'pending': ('warning', 'En attente'),
            'paid': ('info', 'Payée'),
            'processing': ('primary', 'En préparation'),
            'shipped': ('info', 'Expédiée'),
            'delivered': ('success', 'Livrée'),
            'cancelled': ('danger', 'Annulée')
        }
        badge_class, label = badges.get(self.status, ('secondary', 'Inconnu'))
        return f'<span class="badge bg-{badge_class}">{label}</span>'
    
    def get_full_address(self):
        """Retourner l'adresse complète"""
        return f"{self.shipping_address}, {self.shipping_postal_code} {self.shipping_city}, {self.shipping_country}"

    def __repr__(self):
        return f'<Order {self.order_number}>'

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    variant_id = db.Column(db.Integer, db.ForeignKey('product_variant.id'), nullable=True)  # Variante sélectionnée
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    
    product = db.relationship('Product', backref='order_items')
    variant = db.relationship('ProductVariant', backref='order_items')

    def __repr__(self):
        return f'<OrderItem {self.id}>'
