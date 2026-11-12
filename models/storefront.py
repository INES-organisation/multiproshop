"""
Boutiques et vitrines vendues par MultiProShop (admin MPS › Boutiques et vitrines).

- Boutique : un site de vente à part entière, à sa marque, servi par MPS (vitrine/app.py), ex. Sérénis.
- Vitrine : une rubrique « produits » sur un site de l'écosystème dont ce n'est pas le métier principal,
  ex. le Magasin d'ALIAS (tonyalpha80.com) ou le matériel recommandé par DIGITA (digita.buzz).

Dans les deux cas MPS reste le vendeur (prix, paiement, commande CJ, e-mails). Le code (« slug ») est
celui du champ « Vitrines » des fiches produits et du paramètre ?project= de /api/partner/catalogue.
Les secrets (jeton PARTNER_TOKEN_<CODE>, clé de session d'une boutique) restent dans deploy/.env :
cette table ne garde que les réglages et l'état de publication.
"""
import json
import os
from datetime import datetime

from extensions import db

KINDS = {'boutique': 'Boutique', 'vitrine': 'Vitrine'}
STATUSES = {'preparation': 'En préparation', 'en_ligne': 'En ligne', 'pause': 'En pause'}

# Réglages de départ : repris tels quels de ce qui tourne déjà (deploy/.env, vitrine/app.py, partner_api).
# order_label est la mention « Commande passée sur … » des commandes : elle sert à les retrouver par site,
# elle ne change donc jamais après la création.
DEFAULTS = [
    {'slug': 'serenis', 'name': 'Sérénis', 'kind': 'boutique', 'status': 'en_ligne',
     'url': 'https://serenis.multiproshop.com', 'order_label': 'serenis.multiproshop.com',
     'tagline': 'Le rituel du soir : sommeil, détente et cocooning', 'color': '#e0975a',
     'hero_product_id': 20987, 'delivery_days': '12-20', 'ines_prefix': 'SERENIS_'},
    {'slug': 'tonyalpha', 'name': 'ALIAS · Tony Alpha 8.0', 'kind': 'vitrine', 'status': 'preparation',
     'url': 'https://tonyalpha80.com/magasin', 'order_label': 'tonyalpha80.com (ALIAS)',
     'tagline': "Le Magasin « Avec quoi ? » : s'équiper pour lancer et faire tourner son activité",
     'color': '#2563eb', 'delivery_days': '12-20', 'ines_prefix': 'TONYALPHA_'},
    {'slug': 'digita', 'name': 'DIGITA', 'kind': 'vitrine', 'status': 'preparation',
     'url': 'https://digita.buzz/boutique', 'order_label': 'digita.buzz',
     'tagline': "Le matériel recommandé par l'agence : créer son contenu et rendre son commerce visible",
     'color': '#7c3aed', 'delivery_days': '12-20', 'ines_prefix': 'DIGITA_'},
]


class Storefront(db.Model):
    __tablename__ = 'storefront'

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(30), unique=True, nullable=False)  # code projet : minuscules, chiffres, tirets
    name = db.Column(db.String(80), nullable=False)
    kind = db.Column(db.String(10), nullable=False, default='vitrine')
    status = db.Column(db.String(12), nullable=False, default='preparation')
    url = db.Column(db.String(200), nullable=True)
    order_label = db.Column(db.String(80), nullable=False)
    tagline = db.Column(db.String(200), nullable=True)
    color = db.Column(db.String(9), nullable=True)
    hero_product_id = db.Column(db.Integer, nullable=True)
    delivery_days = db.Column(db.String(10), nullable=True)  # « 12-20 »
    free_shipping_threshold = db.Column(db.Float, nullable=True)  # vide : FREE_SHIPPING_THRESHOLD_<CODE>, puis MPS
    lots = db.Column(db.Text, nullable=True)  # JSON [{"name", "text", "ids": [...]}] : lots de l'accueil d'une boutique
    ines_prefix = db.Column(db.String(30), nullable=True)  # préfixe des réglages dans INES › /admin/integrations
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def env_key(self):
        return self.slug.upper().replace('-', '_')

    @property
    def token_configured(self):
        return len(os.environ.get(f'PARTNER_TOKEN_{self.env_key}', '')) >= 24

    @property
    def kind_label(self):
        return KINDS.get(self.kind, self.kind)

    @property
    def status_label(self):
        return STATUSES.get(self.status, self.status)

    def get_lots(self):
        try:
            lots = json.loads(self.lots) if self.lots else []
        except ValueError:
            return []
        return lots if isinstance(lots, list) else []

    def public_json(self):
        """Réglages lus par la boutique (vitrine/app.py) et les vitrines : rien de secret"""
        return {'project': self.slug, 'name': self.name, 'kind': self.kind, 'status': self.status,
                'url': self.url, 'tagline': self.tagline, 'color': self.color,
                'hero_product_id': self.hero_product_id, 'delivery_days': self.delivery_days,
                'lots': self.get_lots()}


def ensure_defaults():
    """Crée une fois les boutiques et vitrines qui existent déjà (aucune modification ensuite)"""
    known = {s for (s,) in db.session.query(Storefront.slug)}
    for d in DEFAULTS:
        if d['slug'] not in known:
            db.session.add(Storefront(**d))
    db.session.commit()


def get(slug):
    return Storefront.query.filter_by(slug=slug).first() if slug else None
