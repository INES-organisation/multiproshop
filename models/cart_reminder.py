"""
Relances de panier abandonné : l'e-mail saisi au paiement et le contenu du panier,
pour 3 rappels (1 h, 24 h, 72 h) tant que la commande n'est pas payée.
"""
from datetime import datetime
import json
import secrets

from extensions import db


class CartReminder(db.Model):
    __tablename__ = 'cart_reminder'

    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(64), unique=True, nullable=False, default=lambda: secrets.token_urlsafe(32))
    email = db.Column(db.String(120), nullable=False, index=True)
    items = db.Column(db.Text, nullable=False, default='{}')  # panier de session (JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)  # dernière activité du client
    steps_sent = db.Column(db.Integer, default=0, nullable=False)
    last_sent_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)  # commande payée
    stopped_at = db.Column(db.DateTime, nullable=True)    # désinscription ou relances terminées

    def get_items(self):
        try:
            return json.loads(self.items or '{}')
        except ValueError:
            return {}
