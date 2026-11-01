"""Traduction des noms de couleur anglais venus de CJ dans les libellés de variantes (« Blue » → « Bleu »)"""
import re

# Expressions de plusieurs mots d'abord, pour que « Navy Blue » ne devienne pas « Navy Bleu »
COLORS = [
    ('navy blue', 'bleu marine'), ('sky blue', 'bleu ciel'), ('light blue', 'bleu clair'), ('dark blue', 'bleu foncé'),
    ('royal blue', 'bleu roi'), ('lake blue', 'bleu lac'), ('light grey', 'gris clair'), ('light gray', 'gris clair'),
    ('dark grey', 'gris foncé'), ('dark gray', 'gris foncé'), ('dark green', 'vert foncé'), ('light green', 'vert clair'),
    ('army green', 'vert militaire'), ('olive green', 'vert olive'), ('mint green', 'vert menthe'), ('rose red', 'rouge rosé'),
    ('wine red', 'bordeaux'), ('light pink', 'rose clair'), ('hot pink', 'rose vif'), ('rose gold', 'or rose'),
    ('light brown', 'marron clair'), ('dark brown', 'marron foncé'), ('off white', 'blanc cassé'), ('off-white', 'blanc cassé'),
    ('black', 'noir'), ('white', 'blanc'), ('blue', 'bleu'), ('red', 'rouge'), ('green', 'vert'), ('yellow', 'jaune'),
    ('pink', 'rose'), ('purple', 'violet'), ('orange', 'orange'), ('grey', 'gris'), ('gray', 'gris'), ('brown', 'marron'),
    ('beige', 'beige'), ('khaki', 'kaki'), ('navy', 'bleu marine'), ('gold', 'doré'), ('golden', 'doré'), ('silver', 'argenté'),
    ('transparent', 'transparent'), ('clear', 'transparent'), ('coffee', 'café'), ('apricot', 'abricot'), ('wine', 'bordeaux'),
    ('burgundy', 'bordeaux'), ('champagne', 'champagne'), ('camel', 'camel'), ('violet', 'violet'), ('lavender', 'lavande'),
    ('turquoise', 'turquoise'), ('cyan', 'cyan'), ('multicolor', 'multicolore'), ('multicolour', 'multicolore'),
    ('colorful', 'multicolore'), ('random', 'aléatoire'), ('leopard', 'léopard'), ('camouflage', 'camouflage'),
]
_PATTERN = re.compile(r'(?<![A-Za-zÀ-ÿ])(' + '|'.join(re.escape(en) for en, _ in COLORS) + r')(?![A-Za-zÀ-ÿ])', re.IGNORECASE)
_MAP = dict(COLORS)


def translate_colors(label):
    """Remplace les couleurs anglaises connues, mot entier, en gardant la majuscule initiale"""
    if not label or not isinstance(label, str):
        return label

    def repl(m):
        fr = _MAP[m.group(1).lower()]
        return fr[0].upper() + fr[1:] if m.group(1)[0].isupper() else fr

    return _PATTERN.sub(repl, label)
