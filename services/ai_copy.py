"""Rédaction en français d'une fiche produit CJ par Claude, via INES (POST /api/v1/generate).

INES fournit Claude aux sites externes avec la même clé que les e-mails (INES_API_KEY). Une génération
par produit : titre, accroche, puces, description, caractéristiques, titre et description Google, et
libellés d'options. Le texte est vérifié (JSON, longueurs, balises autorisées) avant d'être enregistré.
"""
import json
import logging
import os
import re
from html import escape
from html.parser import HTMLParser

import requests

logger = logging.getLogger(__name__)

MODEL = os.getenv('INES_COPY_MODEL', 'claude-sonnet-5')
TIMEOUT = 120

SYSTEM = """Tu es rédacteur e-commerce pour MultiProShop, boutique en ligne française.
Tu réécris en français des fiches produit de fournisseur (souvent en anglais approximatif).
Règles :
- N'invente rien : seulement les informations présentes dans la source (dimensions, matière, contenu…).
- Pas de marque déposée sauf si elle est le nom générique du produit ; pas d'allégation santé ou médicale ;
  pas de promesse de livraison, de délai, de garantie ou de prix.
- Ton clair et concret, vouvoiement, phrases courtes, pas de superlatifs creux.
- Titre : nom de produit naturel en français, 70 caractères au plus, sans majuscules à chaque mot.
- Réponds uniquement avec un objet JSON valide, sans texte autour."""

PROMPT = """Source fournisseur :
Titre : {name}
Catégorie : {category}
Matière : {material}
Options proposées : {options}
Description :
{description}

Rends ce JSON :
{{
  "name": "titre français, 70 caractères max",
  "intro": "1 ou 2 phrases d'accroche sur le bénéfice principal",
  "bullets": ["3 à 5 points forts, 90 caractères max chacun"],
  "details_html": "<p>…</p> puis éventuellement <h3>Caractéristiques</h3><ul><li>…</li></ul> et <h3>Contenu du colis</h3><ul>…</ul> ; balises autorisées : p, ul, li, h3, strong, br",
  "specs": {{"Matière": "…", "Dimensions": "…"}},
  "meta_title": "titre Google, 60 caractères max",
  "meta_description": "description Google, 150 caractères max",
  "options": {{"libellé d'origine": "libellé français court"}}
}}
Dans "options", traduis chaque libellé d'option listé ci-dessus (couleurs, tailles, lots), sans changer les tailles
standard (S, M, L, XL, 38…). Omets "specs" si la source ne donne aucune caractéristique."""


class CopyError(Exception):
    pass


def enabled():
    return bool(os.getenv('INES_API_KEY'))


def _generate(system, prompt, max_tokens=3000):
    url = os.getenv('INES_API_URL', 'http://ines-backend:8000').rstrip('/') + '/api/v1/generate'
    try:
        r = requests.post(url, json={'system': system, 'prompt': prompt, 'model': MODEL, 'max_tokens': max_tokens,
                                     'temperature': 0.3},
                          headers={'Authorization': 'Bearer ' + os.getenv('INES_API_KEY', '')}, timeout=TIMEOUT)
    except requests.RequestException as e:
        raise CopyError(f'INES injoignable : {e}') from e
    if r.status_code == 402:
        raise CopyError('crédits INES insuffisants pour la rédaction par Claude')
    if r.status_code >= 400:
        try:
            detail = r.json().get('detail')
        except ValueError:
            detail = None
        raise CopyError(f'INES a refusé la rédaction ({detail or "HTTP %d" % r.status_code})')
    body = r.json()
    logger.info(f"[Copy] {body.get('model')} {body.get('duration_ms')} ms, {body.get('cost_usd')} $")
    return body.get('text') or ''


class _Sanitizer(HTMLParser):
    ALLOWED = {'p', 'ul', 'ol', 'li', 'h3', 'h4', 'strong', 'em', 'br'}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []

    def handle_starttag(self, tag, attrs):
        if tag in self.ALLOWED:
            self.out.append(f'<{tag}>')

    def handle_endtag(self, tag):
        if tag in self.ALLOWED and tag != 'br':
            self.out.append(f'</{tag}>')

    def handle_data(self, data):
        self.out.append(escape(data, quote=False))


def sanitize(html):
    parser = _Sanitizer()
    parser.feed(html or '')
    parser.close()
    return ''.join(parser.out).strip()


def _plain(html, limit=4000):
    text = re.sub(r'<(br|/p|/li|/h\d|/tr)[^>]*>', '\n', html or '', flags=re.I)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n\s*\n+', '\n', text).strip()
    return text[:limit]


def _parse(text):
    text = text.strip()
    text = re.sub(r'^```(?:json)?\s*|\s*```$', '', text)
    start, end = text.find('{'), text.rfind('}')
    if start < 0 or end <= start:
        raise CopyError('réponse de Claude illisible')
    try:
        data = json.loads(text[start:end + 1])
    except ValueError as e:
        raise CopyError('réponse de Claude illisible') from e
    name = (data.get('name') or '').strip()
    if not name or len(name) > 120:
        raise CopyError('titre généré invalide')
    return data


def option_labels(product):
    from models.product_variant import ProductVariant
    labels = []
    for v in ProductVariant.query.filter_by(product_id=product.id, active=True).all():
        for label in (v.color, v.size):
            if label and label not in labels:
                labels.append(label)
    return labels[:60]


def generate(product):
    """Textes français pour un produit (dict validé). Lève CopyError si INES ou Claude échoue."""
    if not enabled():
        raise CopyError('INES_API_KEY absente : rédaction par Claude impossible')
    options = option_labels(product)
    prompt = PROMPT.format(
        name=product.name, category=product.category.name if product.category else '',
        material=product.material or '', options=' | '.join(options) or 'aucune',
        description=_plain(product.description) or '(aucune)')
    return _parse(_generate(SYSTEM, prompt))


def apply(product, data):
    """Enregistre les textes générés sur le produit et ses variantes actives"""
    from models.product_variant import ProductVariant
    product.name = data['name'].strip()[:255]
    intro = (data.get('intro') or '').strip()
    details = sanitize(data.get('details_html') or '')
    product.description = (f'<p>{escape(intro)}</p>' if intro else '') + details
    bullets = [re.sub(r'\s+', ' ', str(b)).strip()[:120] for b in (data.get('bullets') or []) if str(b).strip()]
    if bullets:
        product.short_description = '\n'.join(bullets[:5])[:500]
    specs = data.get('specs')
    if isinstance(specs, dict):
        specs = {str(k)[:60]: str(v)[:200] for k, v in specs.items() if str(v).strip()}
        if specs:
            product.set_specifications_dict(specs)
    if data.get('meta_title'):
        product.meta_title = str(data['meta_title']).strip()[:70]
    if data.get('meta_description'):
        product.meta_description = str(data['meta_description']).strip()[:160]
    labels = data.get('options') if isinstance(data.get('options'), dict) else {}
    if labels:
        for v in ProductVariant.query.filter_by(product_id=product.id, active=True).all():
            if v.color in labels and str(labels[v.color]).strip():
                v.color = str(labels[v.color]).strip()[:150]
            if v.size in labels and str(labels[v.size]).strip():
                v.size = str(labels[v.size]).strip()[:150]


_FR = {'le', 'la', 'les', 'des', 'pour', 'avec', 'et', 'en', 'de', 'du', 'une', 'un', 'sans', 'au', 'aux'}
_EN = {'the', 'and', 'for', 'with', 'of', 'to', 'in', 'men', 'women', 'mens', 'womens', 'set', 'new', 'style'}


def looks_french(product):
    """Fiche déjà rédigée en français (à la main ou par une génération précédente) ?"""
    if product.meta_description:
        return True
    words = re.findall(r"[a-zà-ÿ']+", (product.name + ' ' + _plain(product.description, 800)).lower())
    fr = sum(w in _FR for w in words)
    en = sum(w in _EN for w in words)
    return fr >= 2 and fr > en
