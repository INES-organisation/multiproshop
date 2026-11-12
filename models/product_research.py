"""
Recherche de produits (admin MPS › Recherche de produits) : veilles et leurs résultats.

Une veille = un site (code de boutique ou vitrine), des recherches et des critères CJ. Chaque passage
compare la demande sur le web (DataForSEO : Amazon.fr, Google Shopping, Google Trends, si branché) à ce
que CJ propose, et range chaque produit : dispo chez CJ, à sourcer, ou écarté. Rien n'est importé sans
un clic dans l'admin, et toujours en brouillon.
"""
import json
from datetime import datetime

from extensions import db

VERDICTS = {
    'dispo': 'Dispo chez CJ',
    'a_sourcer': 'À sourcer',
    'info': 'Repère du marché',
    'ecarte': 'Écarté',
    'importe': 'Importé en brouillon',
    'sourcing': 'Envoyé au sourcing CJ',
}

DEFAULT_CRITERIA = {'min_cost': 1.5, 'max_cost': 45.0, 'min_images': 4, 'max_weight': 2500, 'min_stock': 50,
                    'per_query': 2, 'candidates': 50, 'max_examined': 6, 'france_only': False}


class ResearchWatch(db.Model):
    __tablename__ = 'research_watch'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    storefront = db.Column(db.String(30), nullable=True)  # code du site où importer (serenis, tonyalpha…)
    # [{"fr": "Micro-cravate sans fil", "q": "wireless lavalier microphone", "must": ["lavalier|lapel", "mic"]}]
    queries = db.Column(db.Text, nullable=False, default='[]')
    criteria = db.Column(db.Text, nullable=True)  # JSON, voir DEFAULT_CRITERIA
    web = db.Column(db.Boolean, default=True)  # comparer au web (DataForSEO) quand il est branché
    active = db.Column(db.Boolean, default=True)  # relancée chaque lundi
    last_run_at = db.Column(db.DateTime, nullable=True)
    last_run_note = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    results = db.relationship('ResearchResult', backref='watch', lazy='dynamic', cascade='all, delete-orphan')

    def get_queries(self):
        try:
            data = json.loads(self.queries or '[]')
        except ValueError:
            return []
        return [q for q in data if isinstance(q, dict) and q.get('fr')]

    def get_criteria(self):
        try:
            data = json.loads(self.criteria) if self.criteria else {}
        except ValueError:
            data = {}
        return {**DEFAULT_CRITERIA, **{k: v for k, v in data.items() if k in DEFAULT_CRITERIA}}


class ResearchResult(db.Model):
    __tablename__ = 'research_result'
    __table_args__ = (db.UniqueConstraint('watch_id', 'kind', 'ref', name='uq_research_result'),)

    id = db.Column(db.Integer, primary_key=True)
    watch_id = db.Column(db.Integer, db.ForeignKey('research_watch.id'), nullable=False, index=True)
    search = db.Column(db.String(120), nullable=False)  # la recherche, en français (titre)
    kind = db.Column(db.String(10), nullable=False)  # cj | amazon | shopping
    ref = db.Column(db.String(80), nullable=False)  # pid CJ, ASIN, identifiant Google
    title = db.Column(db.String(300), nullable=False)
    image = db.Column(db.String(500), nullable=True)
    url = db.Column(db.String(500), nullable=True)
    price_eur = db.Column(db.Float, nullable=True)  # CJ : notre prix de vente ; web : prix constaté
    cost_eur = db.Column(db.Float, nullable=True)  # CJ seulement
    listed = db.Column(db.Integer, nullable=True)  # CJ : boutiques qui le vendent
    bought_month = db.Column(db.Integer, nullable=True)  # Amazon : « acheté le mois dernier »
    rating = db.Column(db.Float, nullable=True)
    votes = db.Column(db.Integer, nullable=True)
    market_price = db.Column(db.Float, nullable=True)  # prix médian du web pour la recherche
    trend = db.Column(db.Integer, nullable=True)  # Google Trends, moyenne sur 12 mois (0-100)
    verdict = db.Column(db.String(12), nullable=False, default='info')
    note = db.Column(db.String(200), nullable=True)
    data = db.Column(db.Text, nullable=True)  # JSON : ce qu'il faut pour importer (CJ)
    product_id = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def verdict_label(self):
        return VERDICTS.get(self.verdict, self.verdict)

    def get_data(self):
        try:
            return json.loads(self.data) if self.data else {}
        except ValueError:
            return {}
