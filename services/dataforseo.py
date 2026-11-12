"""
DataForSEO (https://dataforseo.com) : la demande sur le web, pour la recherche de produits.

- Google Trends : intérêt moyen sur 12 mois en France (0-100), 5 recherches par appel (0,011 $).
- Amazon.fr : les produits d'une recherche avec « acheté le mois dernier », note et prix (0,003 $).
- Google Shopping : les produits d'une recherche, prix et avis (0,002 $).
Amazon et Shopping passent par une tâche (task_post) relue jusqu'à ce qu'elle soit prête (task_get),
en priorité haute : moins d'une minute en général.

Identifiants (compte DataForSEO › API Access) : DATAFORSEO_LOGIN et DATAFORSEO_PASSWORD, dans INES
› /admin/integrations (préfixe MULTIPROSHOP_) ou deploy/.env. Sans eux, la recherche se fait sur CJ seul.
"""
import logging
import os
import time

import requests

logger = logging.getLogger(__name__)

API = 'https://api.dataforseo.com/v3/'
FRANCE = 2250  # location_code de la France chez DataForSEO
READY, IN_QUEUE = 20000, {40601, 40602}  # tâche prête ; tâche reçue ou en file


class DataForSEOError(Exception):
    pass


def credentials():
    login = os.getenv('DATAFORSEO_LOGIN') or os.getenv('MULTIPROSHOP_DATAFORSEO_LOGIN')
    password = os.getenv('DATAFORSEO_PASSWORD') or os.getenv('MULTIPROSHOP_DATAFORSEO_PASSWORD')
    return (login, password) if login and password else None


def configured():
    return credentials() is not None


class DataForSEO:
    def __init__(self, auth=None, wait=120, poll=5):
        self.auth = auth or credentials()
        if not self.auth:
            raise DataForSEOError('DataForSEO non branché (DATAFORSEO_LOGIN / DATAFORSEO_PASSWORD)')
        self.wait, self.poll = wait, poll
        self.cost = 0.0  # dépense de cette session, en dollars

    def _call(self, method, path, body=None):
        try:
            r = requests.request(method, API + path, json=body, auth=self.auth, timeout=60)
        except requests.RequestException as e:
            raise DataForSEOError(f'DataForSEO injoignable : {e}') from e
        if r.status_code == 401:
            raise DataForSEOError('identifiants DataForSEO refusés')
        if r.status_code == 402:
            raise DataForSEOError('crédit DataForSEO épuisé')
        try:
            data = r.json()
        except ValueError as e:
            raise DataForSEOError(f'réponse DataForSEO illisible (HTTP {r.status_code})') from e
        if data.get('status_code') != READY:
            raise DataForSEOError(data.get('status_message') or f'HTTP {r.status_code}')
        task = (data.get('tasks') or [{}])[0]
        self.cost += float(task.get('cost') or 0)
        return task

    def _task(self, path, params):
        """Lance une tâche et attend son résultat"""
        task = self._call('POST', f'{path}/task_post', [dict(params, priority=2)])
        if task.get('status_code') != 20100:
            raise DataForSEOError(task.get('status_message') or 'tâche refusée')
        deadline = time.time() + self.wait
        while True:
            time.sleep(self.poll)
            done = self._call('GET', f"{path}/task_get/advanced/{task['id']}")
            if done.get('status_code') == READY:
                return ((done.get('result') or [{}])[0] or {}).get('items') or []
            if done.get('status_code') not in IN_QUEUE:
                raise DataForSEOError(done.get('status_message') or 'tâche en échec')
            if time.time() > deadline:
                raise DataForSEOError('DataForSEO trop lent, réessayer plus tard')

    def trends(self, keywords):
        """{recherche: intérêt moyen sur 12 mois en France, 0-100}. Les valeurs se comparent entre elles :
        Google ramène la plus demandée du lot à 100."""
        out = {}
        for i in range(0, len(keywords), 5):
            batch = keywords[i:i + 5]
            task = self._call('POST', 'keywords_data/google_trends/explore/live', [{
                'keywords': batch, 'location_code': FRANCE, 'language_code': 'fr',
                'time_range': 'past_12_months', 'item_types': ['google_trends_graph']}])
            items = ((task.get('result') or [{}])[0] or {}).get('items') or []
            graph = next((it for it in items if it.get('type') == 'google_trends_graph'), {})
            points = [p.get('values') or [] for p in graph.get('data') or [] if not p.get('missing_data')]
            for n, kw in enumerate(batch):
                values = [v[n] for v in points if n < len(v) and v[n] is not None]
                out[kw] = round(sum(values) / len(values)) if values else None
        return out

    def amazon(self, keyword, depth=20):
        items = self._task('merchant/amazon/products', {
            'keyword': keyword, 'location_code': FRANCE, 'language_code': 'fr_FR', 'se_domain': 'amazon.fr',
            'depth': depth})
        out = []
        for it in items:
            if not it.get('data_asin') or not it.get('title'):
                continue
            rating = it.get('rating') or {}
            out.append({'kind': 'amazon', 'ref': it['data_asin'], 'title': it['title'], 'url': it.get('url'),
                        'image': it.get('image_url'), 'price': _eur(it.get('price_from'), it.get('currency')),
                        'rating': _num(rating.get('value')), 'votes': _int(rating.get('votes_count')),
                        'bought_month': _int(it.get('bought_past_month')),
                        'best_seller': bool(it.get('is_best_seller'))})
        return out

    def shopping(self, keyword, depth=20):
        items = self._task('merchant/google/products', {
            'keyword': keyword, 'location_code': FRANCE, 'language_code': 'fr', 'depth': depth})
        out = []
        for it in items:
            ref = it.get('product_id') or it.get('data_docid')
            if not ref or not it.get('title'):
                continue
            rating = it.get('product_rating') or {}
            out.append({'kind': 'shopping', 'ref': str(ref), 'title': it['title'],
                        'url': it.get('shopping_url') or it.get('url'),
                        'image': (it.get('product_images') or [None])[0],
                        'price': _eur(it.get('price'), it.get('currency')),
                        'rating': _num(rating.get('value')),
                        'votes': _int(rating.get('votes_count') or it.get('reviews_count')),
                        'seller': it.get('seller')})
        return out


def _num(v):
    try:
        return float(v) if v is not None else None
    except (TypeError, ValueError):
        return None


def _int(v):
    n = _num(v)
    return int(n) if n is not None else None


def _eur(price, currency):
    """Prix en euros ; un prix dans une autre monnaie n'est pas comparé"""
    p = _num(price)
    return p if p and (currency or 'EUR').upper() == 'EUR' else None
