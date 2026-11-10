"""Comptage des visiteurs uniques du jour (voir models.visit)."""
import hashlib
import hmac
import re
from datetime import date

from flask import current_app, request

BOTS = re.compile(r'bot|crawl|spider|slurp|preview|monitor|curl|wget|python|headless|lighthouse', re.I)
SKIP = ('/static', '/admin', '/api', '/favicon', '/robots', '/sitemap', '/health')
_seen = set()  # ponytail: évite une écriture par page ; vidé chaque jour, plafonné à 50 000 empreintes


def track():
    """À appeler avant chaque requête : n'écrit qu'à la première page HTML du visiteur dans la journée."""
    if request.method != 'GET' or request.path.startswith(SKIP) or 'text/html' not in request.headers.get('Accept', ''):
        return
    agent = request.headers.get('User-Agent', '')
    if not agent or BOTS.search(agent):
        return
    ip = (request.headers.get('X-Forwarded-For') or request.remote_addr or '').split(',')[0].strip()
    today = date.today()
    key = current_app.config['SECRET_KEY'] or ''
    fingerprint = hmac.new(str(key).encode(), f'{today}|{ip}|{agent}'.encode(), hashlib.sha256).hexdigest()[:32]
    if (today, fingerprint) in _seen:
        return
    if len(_seen) > 50000 or any(d != today for d, _ in list(_seen)[:1]):
        _seen.clear()
        _purge(today)
    _seen.add((today, fingerprint))
    from extensions import db
    from models.visit import VisitorDay
    try:
        if not VisitorDay.query.filter_by(day=today, fingerprint=fingerprint).first():
            db.session.add(VisitorDay(day=today, fingerprint=fingerprint))
            db.session.commit()
    except Exception:  # course entre deux workers (contrainte unique) : le visiteur est déjà compté
        db.session.rollback()


def _purge(today):
    """Les empreintes ne servent qu'au dédoublonnage : rien n'est gardé au-delà de 400 jours."""
    from datetime import timedelta
    from extensions import db
    from models.visit import VisitorDay
    try:
        VisitorDay.query.filter(VisitorDay.day < today - timedelta(days=400)).delete()
        db.session.commit()
    except Exception:
        db.session.rollback()


def visits(since):
    """Visites depuis `since` : au plus une par visiteur et par jour."""
    from extensions import db
    from models.visit import VisitorDay
    return db.session.query(db.func.count(VisitorDay.id)).filter(VisitorDay.day >= since).scalar() or 0
