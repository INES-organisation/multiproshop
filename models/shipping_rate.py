"""
Modèle ShippingRate - Cache des frais de livraison CJ par produit × pays
Stratégie hybride : pré-sync en DB + refresh si données > 7 jours
"""
from extensions import db
from datetime import datetime, timedelta
import json


class ShippingRate(db.Model):
    """Cache des méthodes de livraison CJ pour un produit et un pays"""
    __tablename__ = 'shipping_rate'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    country_code = db.Column(db.String(5), nullable=False)  # FR, BE, CH, LU...
    
    # Méthodes de livraison (JSON array)
    # Ex: [{"code": "USPS+", "name": "USPS+", "price": 4.71, "delivery_time": "2-5", "source": "cj"}]
    methods_json = db.Column(db.Text, nullable=False, default='[]')
    
    # Source des données
    source = db.Column(db.String(20), default='cj')  # 'cj' ou 'fallback'
    
    # Timestamps
    synced_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Contrainte unique : un seul enregistrement par produit × pays
    __table_args__ = (
        db.UniqueConstraint('product_id', 'country_code', name='uq_shipping_rate_product_country'),
    )
    
    # Relations
    product = db.relationship('Product', backref=db.backref('shipping_rates', lazy='dynamic'))
    
    def __repr__(self):
        return f'<ShippingRate product={self.product_id} country={self.country_code}>'
    
    @property
    def methods(self):
        """Retourne les méthodes de livraison en liste de dicts"""
        try:
            return json.loads(self.methods_json)
        except (json.JSONDecodeError, TypeError):
            return []
    
    @methods.setter
    def methods(self, value):
        """Définit les méthodes de livraison depuis une liste de dicts"""
        self.methods_json = json.dumps(value, ensure_ascii=False)
    
    def is_expired(self, max_age_days=7):
        """Vérifie si les données sont expirées"""
        if not self.synced_at:
            return True
        return datetime.utcnow() - self.synced_at > timedelta(days=max_age_days)
    
    def has_methods(self):
        """Vérifie si des méthodes sont disponibles"""
        return len(self.methods) > 0
    
    @classmethod
    def get_for_product(cls, product_id, country_code):
        """Récupérer le cache shipping pour un produit et un pays"""
        return cls.query.filter_by(
            product_id=product_id,
            country_code=country_code
        ).first()
    
    @classmethod
    def get_for_products(cls, product_ids, country_code):
        """Récupérer le cache shipping pour plusieurs produits et un pays"""
        return cls.query.filter(
            cls.product_id.in_(product_ids),
            cls.country_code == country_code
        ).all()
    
    @classmethod
    def upsert(cls, product_id, country_code, methods, source='cj'):
        """Créer ou mettre à jour un cache shipping"""
        rate = cls.get_for_product(product_id, country_code)
        if rate:
            rate.methods = methods
            rate.source = source
            rate.synced_at = datetime.utcnow()
        else:
            rate = cls(
                product_id=product_id,
                country_code=country_code,
                source=source
            )
            rate.methods = methods
            db.session.add(rate)
        return rate
    
    @classmethod
    def get_countries_for_product(cls, product_id):
        """Liste des pays disponibles pour un produit"""
        rates = cls.query.filter_by(product_id=product_id).all()
        return [r.country_code for r in rates if r.has_methods()]
