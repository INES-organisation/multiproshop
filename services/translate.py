"""Traduction fidèle par DeepL, via INES (POST /api/v1/external/translate, clé DEEPL_API_KEY dans INES).

Partage des rôles : DeepL traduit à l'identique les textes courts (libellés d'options…), Claude
(services/ai_copy) réécrit la fiche de vente. Si DeepL n'est pas configuré dans INES ou ne répond pas,
les fonctions renvoient None et l'appelant laisse Claude faire. Chaque traduction est gardée 90 jours
en cache : un même libellé n'est jamais payé deux fois.
"""
import hashlib
import logging
import os

import requests

logger = logging.getLogger(__name__)

TTL = 90 * 24 * 3600
OFF_KEY = 'deepl:off'
BATCH = 50


def _key(text, target, source):
    return 'deepl:%s:%s:%s' % (source or '', target, hashlib.sha1(text.encode('utf-8')).hexdigest())


def _call(texts, target, source, context, html):
    url = os.getenv('INES_API_URL', 'http://ines-backend:8000').rstrip('/') + '/api/v1/external/translate'
    r = requests.post(url, json={'texts': texts, 'target_lang': target, 'source_lang': source, 'context': context,
                                 'html': html},
                      headers={'Authorization': 'Bearer ' + os.getenv('INES_API_KEY', '')}, timeout=20)
    if r.status_code in (404, 503):
        return 'off'  # INES sans DeepL (pas de clé, ou INES pas encore à jour)
    if r.status_code >= 400:
        try:
            detail = r.json().get('detail')
        except ValueError:
            detail = r.text[:200]
        raise RuntimeError(f'DeepL via INES : HTTP {r.status_code} {detail}')
    return [t['text'] for t in r.json()['translations']]


def translate(texts, target='FR', source='EN', context=None, html=False):
    """Liste traduite dans le même ordre, ou None si DeepL est indisponible"""
    from extensions import cache
    if not texts or not os.getenv('INES_API_KEY'):
        return None
    try:
        if cache.get(OFF_KEY):
            return None
    except Exception:
        pass
    out = {}
    todo = []
    for text in dict.fromkeys(texts):
        try:
            hit = cache.get(_key(text, target, source))
        except Exception:
            hit = None
        if hit is not None:
            out[text] = hit
        else:
            todo.append(text)
    try:
        for i in range(0, len(todo), BATCH):
            chunk = todo[i:i + BATCH]
            result = _call(chunk, target, source, context, html)
            if result == 'off':
                cache.set(OFF_KEY, 1, timeout=600)
                return None
            for text, translated in zip(chunk, result):
                out[text] = translated
                try:
                    cache.set(_key(text, target, source), translated, timeout=TTL)
                except Exception:
                    pass
    except Exception as e:
        logger.warning(f'[DeepL] {e}')
        return None
    return [out[t] for t in texts]


def translate_options(product):
    """Traduit par DeepL les libellés d'options (couleur, taille) que le traducteur local ne sait pas traduire.
    Renvoie le nombre de libellés traduits, ou None si DeepL est indisponible."""
    from models.product_variant import ProductVariant
    from utils.options_fr import needs_translation
    variants = ProductVariant.query.filter_by(product_id=product.id, active=True).all()
    labels = list(dict.fromkeys(l for v in variants for l in (v.color, v.size) if needs_translation(l)))
    if not labels:
        return 0
    result = translate(labels, context=f"Libellés d'options (couleur, taille, modèle) du produit : {product.name}")
    if result is None:
        return None
    mapping = {a: b.strip()[:150] for a, b in zip(labels, result) if b and b.strip()}
    for v in variants:
        if v.color in mapping:
            v.color = mapping[v.color]
        if v.size in mapping:
            v.size = mapping[v.size]
    return len(mapping)
