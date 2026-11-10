"""
Visiteurs uniques par jour, pour le taux de conversion que lit INES (/api/partner/stats).

Ni cookie ni adresse IP en base : une empreinte HMAC(SECRET_KEY, jour + IP + navigateur) tronquée,
qui change chaque jour, sert seulement à ne compter qu'une fois le même visiteur dans la journée.
"""
from datetime import date

from extensions import db


class VisitorDay(db.Model):
    __tablename__ = 'visitor_day'
    __table_args__ = (db.UniqueConstraint('day', 'fingerprint', name='uq_visitor_day'),)

    id = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.Date, nullable=False, default=date.today, index=True)
    fingerprint = db.Column(db.String(32), nullable=False)
