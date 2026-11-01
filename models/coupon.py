"""Codes promo saisis au paiement"""
from datetime import datetime

from extensions import db


class Coupon(db.Model):
    __tablename__ = 'coupon'

    KINDS = {'percent': 'Pourcentage', 'fixed': 'Montant fixe', 'shipping': 'Livraison offerte'}

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(40), unique=True, nullable=False, index=True)  # en majuscules, sans espace
    kind = db.Column(db.String(20), nullable=False, default='percent')
    value = db.Column(db.Float, nullable=False, default=0)  # % ou € selon kind (ignoré pour la livraison)
    min_subtotal = db.Column(db.Float, nullable=False, default=0)
    starts_at = db.Column(db.DateTime, nullable=True)
    ends_at = db.Column(db.DateTime, nullable=True)
    max_uses = db.Column(db.Integer, nullable=True)  # None = illimité
    uses = db.Column(db.Integer, nullable=False, default=0)  # commandes payées
    once_per_email = db.Column(db.Boolean, nullable=False, default=True)
    active = db.Column(db.Boolean, nullable=False, default=True)
    note = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def label(self):
        if self.kind == 'percent':
            return f'-{self.value:g} %'
        if self.kind == 'fixed':
            return f'-{self.value:.2f} €'.replace('.', ',')
        return 'Livraison offerte'

    def status(self, now=None):
        now = now or datetime.utcnow()
        if not self.active:
            return 'désactivé'
        if self.starts_at and now < self.starts_at:
            return 'à venir'
        if self.ends_at and now > self.ends_at:
            return 'expiré'
        if self.max_uses is not None and self.uses >= self.max_uses:
            return 'épuisé'
        return 'actif'
