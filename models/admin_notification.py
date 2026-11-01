"""Notifications de l'admin : commandes, ruptures, marges, litiges CJ, erreurs de commande CJ"""
from datetime import datetime

from extensions import db


class AdminNotification(db.Model):
    __tablename__ = 'admin_notification'

    id = db.Column(db.Integer, primary_key=True)
    kind = db.Column(db.String(40), nullable=False, index=True)  # order, cj_order_error, stock, margin, dispute…
    level = db.Column(db.String(10), nullable=False, default='info')  # info, success, warning, danger
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=True)
    url = db.Column(db.String(300), nullable=True)
    dedupe_key = db.Column(db.String(120), nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    read_at = db.Column(db.DateTime, nullable=True)
