"""
Demande de sourcing CJ (product/sourcing/create) : on donne à CJ le lien d'un produit (AliExpress,
1688, Taobao…), CJ le trouve, l'ajoute à son catalogue et l'expédie comme ses autres produits.
L'état est relu par product/sourcing/queryList ; une fois trouvé, le produit s'importe en brouillon.
"""
from datetime import datetime

from extensions import db


class CjSourcing(db.Model):
    __tablename__ = 'cj_sourcing'

    id = db.Column(db.Integer, primary_key=True)
    cj_sourcing_id = db.Column(db.String(50), unique=True, nullable=False)
    product_name = db.Column(db.String(200), nullable=False)
    product_url = db.Column(db.String(200), nullable=True)
    product_image = db.Column(db.String(200), nullable=False)
    price_usd = db.Column(db.Float, nullable=True)  # prix cible indiqué à CJ
    remark = db.Column(db.String(200), nullable=True)
    # CJ ne documente que « 3 » (trouvé) et « 5 » (échec) : toute autre valeur = en cours
    status = db.Column(db.String(10), nullable=True)
    status_label = db.Column(db.String(100), nullable=True)
    cj_product_id = db.Column(db.String(50), nullable=True)
    fail_reason = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    checked_at = db.Column(db.DateTime, nullable=True)

    @property
    def found(self):
        return self.status == '3' and bool(self.cj_product_id)

    @property
    def failed(self):
        return self.status == '5'
