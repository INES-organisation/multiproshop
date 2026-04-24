"""
Modèle ProductVariant pour les variantes de produits CJ
Gère les couleurs, tailles et autres options de produits
"""
from extensions import db
from datetime import datetime


class ProductVariant(db.Model):
    """
    Variantes de produits (couleurs, tailles, etc.)
    Inspiré de TonyAlpha80/src/Services/CjSyncService.php
    """
    __tablename__ = 'product_variant'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Relation avec le produit
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    
    # Identifiants CJ
    cj_vid = db.Column(db.String(255), unique=True, nullable=False)  # Variant ID CJ
    variant_key = db.Column(db.String(100), nullable=True)  # Ex: "White-S"
    
    # Options
    color = db.Column(db.String(50), nullable=True)  # Couleur
    size = db.Column(db.String(50), nullable=True)   # Taille
    
    # Prix et stock spécifiques à la variante
    price = db.Column(db.Float, nullable=True)
    suggested_price = db.Column(db.Float, nullable=True)
    stock = db.Column(db.Integer, default=0)
    
    # Image spécifique à la variante
    image_url = db.Column(db.Text, nullable=True)
    
    # Caractéristiques physiques
    weight = db.Column(db.Integer, nullable=True)  # Poids en grammes
    
    # SKU spécifique
    sku = db.Column(db.String(100), nullable=True)
    
    # Statut
    active = db.Column(db.Boolean, default=True)
    
    # Données brutes CJ pour audit
    cj_raw_data = db.Column(db.Text, nullable=True)  # Données brutes CJ (JSON)
    
    # Dates
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relation inverse
    product = db.relationship('Product', backref=db.backref('variants', lazy='dynamic'))
    
    def __repr__(self):
        return f'<ProductVariant {self.variant_key} for Product {self.product_id}>'
    
    def to_dict(self):
        """Convertir en dictionnaire"""
        return {
            'id': self.id,
            'cj_vid': self.cj_vid,
            'variant_key': self.variant_key,
            'color': self.color,
            'size': self.size,
            'price': self.price,
            'suggested_price': self.suggested_price,
            'stock': self.stock,
            'image_url': self.image_url,
            'weight': self.weight,
            'sku': self.sku,
            'active': self.active
        }
    
    @property
    def display_name(self):
        """Nom d'affichage de la variante"""
        parts = []
        if self.color:
            parts.append(self.color)
        if self.size:
            parts.append(self.size)
        return ' - '.join(parts) if parts else self.variant_key or 'Variante'
    
    @property
    def is_in_stock(self):
        """Vérifie si la variante est en stock"""
        return self.stock > 0
    
    def reduce_stock(self, quantity):
        """Réduit le stock de la variante"""
        if self.stock >= quantity:
            self.stock -= quantity
            return True
        return False
