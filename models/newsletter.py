"""Inscrits à la newsletter (code de bienvenue -10 % sur la première commande)"""
import secrets
from datetime import datetime

from extensions import db


class NewsletterSubscriber(db.Model):
    __tablename__ = 'newsletter_subscriber'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    token = db.Column(db.String(64), unique=True, nullable=False, default=lambda: secrets.token_urlsafe(24))
    coupon_code = db.Column(db.String(40), nullable=True)
    source = db.Column(db.String(40), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    unsubscribed_at = db.Column(db.DateTime, nullable=True)
