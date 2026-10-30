"""
Demande d'avis : un e-mail par commande livrée, avec un lien personnel vers le formulaire
(un avis par article). Seuls les clients ayant reçu leur commande peuvent donc noter.
"""
from datetime import datetime
import json
import secrets

from extensions import db


class ReviewRequest(db.Model):
    __tablename__ = 'review_request'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), unique=True, nullable=False)
    token = db.Column(db.String(64), unique=True, nullable=False, default=lambda: secrets.token_urlsafe(32))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    sent_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)  # avis déposé(s) ou demande refusée
    reviewed = db.Column(db.Text, nullable=False, default='[]')  # produits déjà notés (JSON)

    order = db.relationship('Order')

    def reviewed_ids(self):
        return set(json.loads(self.reviewed or '[]'))
