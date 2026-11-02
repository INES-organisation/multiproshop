"""Couleur et taille d'une variante CJ tirées de sa clé (« Khaki-4XL »), pas de son nom.

L'ancien import coupait le nom complet de la variante au premier tiret : « Mens Retro Loose-fit Casual
Athletic Pants Khaki-4XL » donnait la couleur « Mens Retro Loose » et la taille « fit Casual Athletic
Pants Khaki 4XL ». La clé CJ (variantKey) ne contient que les valeurs d'options, séparées par des tirets,
dans l'ordre des noms d'options du produit (productKeyEn, ex. « Color-Size »).
"""
import json
import re

MAX_KEY_LEN = 60  # au-delà, ce n'est pas une clé d'options mais un nom de produit

_SIZE = re.compile(r'size|taille|尺码|code|length|width|capacity|volume|spec', re.I)
_SIZE_VALUE = re.compile(r'^(\d?X{0,3}[SL]|XXS|XS|M|\d{1,3}(\.\d)?\s*(cm|mm|m|ml|l|in|inch|")?|EU\s?\d{2}|US\s?\d{1,2}|One Size|Free Size)$', re.I)
_COLOR = re.compile(r'colou?r|couleur|颜色|style|pattern|model|type', re.I)


def product_key_names(product):
    """Noms des options du produit (« Color-Size » → ['Color', 'Size']), lus dans les données CJ"""
    raw = getattr(product, 'cj_raw_data', None)
    if not raw:
        return []
    try:
        data = json.loads(raw) if isinstance(raw, str) else raw
    except (ValueError, TypeError):
        return []
    if not isinstance(data, dict):
        return []
    key = data.get('productKeyEn') or (data.get('raw_data') or {}).get('productKeyEn') or ''
    if isinstance(key, list):
        return [str(k).strip() for k in key if str(k).strip()]
    return [k.strip() for k in str(key).split('-') if k.strip()]


def split_variant_key(key, names=None):
    """(couleur, taille) d'après la clé CJ, ou None si la clé n'est pas exploitable"""
    key = (key or '').strip()
    if not key or len(key) > MAX_KEY_LEN:
        return None
    n = len(names) if names else (2 if '-' in key else 1)
    if n <= 1:
        values = [key]
    else:
        values = [v.strip() for v in key.split('-')]
        if len(values) != n:
            # Une valeur contient elle-même un tiret (« Off-White-XL ») : la dernière option est la taille
            values = [v.strip() for v in key.rsplit('-', n - 1)] if len(values) > n else values
    values = [v for v in values if v]
    if not values:
        return None
    if names and len(names) == len(values):
        color = size = None
        rest = []
        for name, value in zip(names, values):
            if size is None and _SIZE.search(name):
                size = value
            elif color is None and _COLOR.search(name):
                color = value
            else:
                rest.append(value)
        # Options sans nom reconnu : la première fait office de couleur, les autres de taille
        if color is None and rest:
            color = rest.pop(0)
        if rest:
            size = ' - '.join([size] + rest) if size else ' - '.join(rest)
        return color, size
    if len(values) == 1:
        if _SIZE_VALUE.match(values[0]) or (names and _SIZE.search(names[0])):
            return None, values[0]
        return values[0], None
    return values[0], ' - '.join(values[1:])


def looks_broken(variant):
    """Couleur/taille issues du nom coupé au premier tiret : elles contiennent toutes les valeurs de la clé
    plus un morceau du nom du produit. Un libellé saisi à la main (« Lot gourde noire… ») n'est pas touché."""
    key = (variant.variant_key or '').strip()
    current = ' '.join(x for x in (variant.color, variant.size) if x).strip()
    if not key or len(key) > MAX_KEY_LEN:
        return False
    if not current:
        return True
    values = [v.strip().lower() for v in key.split('-') if v.strip()]
    low = current.lower()
    return all(v in low for v in values) and len(current) > len(key) + 10


def repair_variant(variant, names=None):
    """Recalcule couleur et taille depuis la clé CJ quand elles viennent du nom coupé.
    Renvoie True si la variante a changé."""
    if not looks_broken(variant):
        return False
    parsed = split_variant_key(variant.variant_key, names)
    if not parsed:
        return False
    color, size = parsed
    if (variant.color or None) == color and (variant.size or None) == size:
        return False
    variant.color, variant.size = color, size
    return True
