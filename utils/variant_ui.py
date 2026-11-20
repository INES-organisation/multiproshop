"""
Sélecteur de variantes de la fiche produit : couleur, taille, ou à défaut une liste d'options.

Peu de choix (8 au plus, libellés courts) : des boutons, avec la vignette de la couleur quand elle a sa
photo. Au-delà : une liste déroulante, plus lisible qu'un mur de boutons, avec le prix quand il change d'un
choix à l'autre et « épuisé » pour ce qui n'est plus en stock. Un seul choix possible : il est déjà
sélectionné. Les combinaisons couleur + taille qui n'existent pas sont grisées côté navigateur.
"""
import re

from utils.options_fr import translate_option

MAX_BUTTONS = 8
MAX_BUTTON_CHARS = 120  # longueur cumulée des libellés au-delà de laquelle on passe en liste


def _eur(value):
    return ('%.2f' % value).replace('.', ',') + ' €'


def _natural(text):
    """« Lot 2 » avant « Lot 10 »"""
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', text or '')]


def _mode(values):
    if len(values) == 1:
        return 'single'  # une seule valeur (« USB ») : simple mention, déjà choisie
    if len(values) > MAX_BUTTONS or sum(len(v['label']) for v in values) > MAX_BUTTON_CHARS:
        return 'select'
    return 'buttons'


def build(product):
    """Dimensions et variantes pour le sélecteur, ou None si le produit n'a pas de variante active"""
    from models.product_variant import ProductVariant
    variants = product.variants.filter_by(active=True).order_by(ProductVariant.id).all() if product.variants else []
    if not variants:
        return None
    discount = 1.0
    if getattr(product, 'promotion', None):
        discount = 1 - (product.promotion.discount_percentage or 0) / 100
    items = []
    for v in variants:
        stock = v.stock if (v.stock or 0) > 0 else (product.stock or 0)
        items.append({'id': v.id, 'color': v.color or '', 'size': v.size or '',
                      'option': '' if (v.color or v.size) else str(v.id),
                      'name': v.display_name or v.variant_key or '',
                      'price': round((v.price or product.price or 0) * discount, 2), 'stock': stock,
                      'image': v.image_url or ''})

    keys = [k for k, label in (('color', 'Couleur'), ('size', 'Taille')) if any(i[k] for i in items)]
    labels = {'color': 'Couleur', 'size': 'Taille', 'option': 'Modèle'}
    if not keys:
        keys = ['option']
    else:
        # Variante sans couleur ni taille à côté d'autres qui en ont : on la nomme « Autre » plutôt que de la perdre
        for i in items:
            for k in keys:
                i[k] = i[k] or '—'

    dims = []
    for k in keys:
        seen = {}
        for i in items:
            value = i[k]
            entry = seen.setdefault(value, {'value': value, 'prices': set(), 'stock': 0, 'image': '',
                                            'label': i['name'] if k == 'option' else translate_option(value)})
            entry['prices'].add(i['price'])
            entry['stock'] += i['stock']
            entry['image'] = entry['image'] or i['image']
        values = sorted(seen.values(), key=lambda v: _natural(v['label']))
        all_prices = {p for v in values for p in v['prices']}
        for v in values:
            v['available'] = v['stock'] > 0
            # Prix dans la liste seulement s'il distingue les choix, et s'il est le même pour tout ce choix
            v['price'] = _eur(next(iter(v['prices']))) if len(all_prices) > 1 and len(v['prices']) == 1 else ''
            v.pop('prices')
            v.pop('stock')
        images = len({v['image'] for v in values if v['image']})
        dims.append({'key': k, 'label': labels[k], 'mode': _mode(values), 'values': values,
                     'placeholder': {'color': 'Choisir une couleur…', 'size': 'Choisir une taille…'}.get(k, 'Choisir un modèle…'),
                     'swatches': k == 'color' and images == len(values) and images > 1})
    for i in items:
        i.pop('name')
    return {'dims': dims, 'variants': items}
