"""Traduction à l'affichage des libellés d'options CJ (« Blue 2pcs » → « Bleu 2 pièces »)

La base garde les valeurs CJ d'origine : la traduction ne sert qu'à l'affichage, pour que
la synchronisation et l'historique des commandes restent inchangés.
"""
import re

from utils.colors_fr import COLORS

_L = r'A-Za-zÀ-ÿ'

# Couleurs simples (un mot) : base des règles « light X » → « X clair »
_SIMPLE_COLORS = {en: fr for en, fr in COLORS if ' ' not in en and '-' not in en and ' ' not in fr}
_SIMPLE_COLORS.update({'gold': 'or', 'golden': 'doré', 'coffee': 'café', 'tea': 'thé', 'purple': 'violet',
                       'leopard': 'léopard', 'camel': 'camel', 'pink': 'rose', 'brown': 'marron'})

# Expressions et mots (anglais → français), en minuscules
TERMS = {
    # Fautes de frappe fréquentes chez CJ
    'balck': 'noir', 'bule': 'bleu', 'gellow': 'jaune', 'gules': 'rouge', 'drange': 'orange',
    'choclate': 'chocolat', 'wiht': 'avec', 'colour': 'couleur',
    # Couleurs composées
    'photo color': 'couleur photo', 'picture color': 'couleur photo', 'as shown': 'comme sur la photo',
    'natural color': 'couleur naturelle', 'wood color': 'couleur bois', 'cp color': 'couleur photo',
    'white color': 'blanc', 'caramel colour': 'caramel', 'caramel color': 'caramel',
    'peacock blue': 'bleu paon', 'haze blue': 'bleu brume', 'water blue': 'bleu d’eau', 'sea blue': 'bleu mer',
    'ice blue': 'bleu glacier', 'baby blue': 'bleu layette', 'tiffany blue': 'bleu Tiffany', 'deep blue': 'bleu foncé',
    'water green': 'vert d’eau', 'jade green': 'vert jade', 'grass green': 'vert herbe', 'fresh green': 'vert frais',
    'avocado green': 'vert avocat', 'military green': 'vert militaire', 'armygreen': 'vert militaire',
    'fluorescent green': 'vert fluo', 'fluorescent yellow': 'jaune fluo', 'lemon yellow': 'jaune citron',
    'grayish yellow': 'jaune grisé', 'greyish purple': 'violet grisé', 'silver grey': 'gris argent',
    'silver gray': 'gris argent', 'gun grey': 'gris anthracite', 'gun gray': 'gris anthracite',
    'deep space grey': 'gris sidéral', 'metal silver gray': 'gris argent métal', 'satin gray gold': 'or gris satiné',
    'orange red': 'rouge orangé', 'red wine': 'bordeaux', 'brown red': 'rouge brun', 'cold brown': 'marron froid',
    'light tea': 'thé clair', 'bean paste': 'vieux rose', 'honey pudding': 'miel', 'milky white': 'blanc laiteux',
    'cream white': 'blanc crème', 'creamy white': 'blanc crème', 'ivory white': 'blanc ivoire',
    'ceramic white': 'blanc céramique', 'clouds white': 'blanc nuage', 'pure white': 'blanc pur',
    'elegant white': 'blanc élégant', 'simple white': 'blanc simple', 'silver white': 'blanc argenté',
    'champagne gold': 'or champagne', 'white gold': 'or blanc', 'light gold': 'or clair', 'kc gold': 'or',
    'powerful black': 'noir intense', 'full black': 'tout noir', 'matte black': 'noir mat',
    'brown black gradient': 'dégradé marron noir', 'chocolate gradient': 'dégradé chocolat',
    'light leopard print': 'imprimé léopard clair', 'dark leopard print': 'imprimé léopard foncé',
    'leopard print': 'imprimé léopard', 'dark night camo': 'camouflage nuit', 'camo': 'camouflage',
    'colorful and colorful': 'multicolore',
    # Lots, quantités, modèles
    'accessories suit': 'kit d’accessoires', 'accessories set': 'kit d’accessoires',
    'accessories package': 'pack d’accessoires', 'accessories no suit': 'accessoires sans kit',
    'completer set': 'lot complet', 'filter cotton set': 'lot de cotons filtrants', 'filter cotton': 'coton filtrant',
    'basic payment': 'modèle de base', 'induction style': 'modèle à détection', 'replacement': 'pièce de rechange',
    'finished product': 'produit fini', 'materials kit': 'kit de matériaux', 'tea set': 'service à thé',
    'upgraded version': 'version améliorée', 'smart version': 'version connectée',
    'low configuration version': 'version de base', 'standard edition': 'édition standard',
    'battery version': 'version à piles', 'battery models': 'modèle à piles', 'battery model': 'modèle à piles',
    'base version': 'version avec socle', 'not luminous': 'non lumineux', 'luminous': 'lumineux',
    'default title': 'standard', 'defaulttitle': 'standard', 'default': 'standard',
    'average size': 'taille moyenne', 'oversized': 'très grand',
    # Animaux et maison
    'garbage bag': 'sac poubelle', 'single traction rope': 'laisse simple', 'traction rope': 'laisse',
    'drinking water and feeding': 'eau et nourriture', 'water and food cup': 'gobelet eau et nourriture',
    'water cup': 'gobelet d’eau', 'water bowl': 'gamelle d’eau', 'feeder': 'distributeur de croquettes',
    'pet head massager': 'masseur de tête pour animal', 'cat litter shovel': 'pelle à litière',
    'sisal post': 'poteau en sisal', 'cage wall type': 'modèle mural pour cage', 'wall type': 'modèle mural',
    'floor mounted': 'modèle sur pied', 'pillow case': 'housse de coussin', 'bite string style': 'modèle corde à mâcher',
    'aeration pump': 'pompe à air', 'dog print': 'motif chien', 'with stickers': 'avec autocollants',
    'ferris wheel': 'grande roue', 'wood grain speaker': 'enceinte veinage bois', 'wood grain': 'veinage bois',
    'wood box': 'boîte en bois', 'tea box': 'boîte à thé', 'big frame': 'grand cadre', 'gun frame': 'cadre anthracite',
    'warm white light': 'lumière blanc chaud', 'white light': 'lumière blanche', 'light strip': 'ruban lumineux',
    'remote control': 'télécommande', 'remote contro': 'télécommande', 'eu plug': 'prise EU', 'us plug': 'prise US',
    'usplug': 'prise US', 'uk plug': 'prise UK', 'no card': 'sans carte', 'english manual': 'notice en anglais',
    'aerial photography': 'photo aérienne', 'dual camera': 'double caméra', 'camera head': 'tête de caméra',
    'cooling handle': 'poignée refroidissante', 'built in clip': 'pince intégrée', 'phone clip': 'pince téléphone',
    'word clip': 'pince', 'digital display': 'affichage numérique', 'digital screen': 'écran numérique',
    'humidifying air cooler': 'rafraîchisseur d’air humidificateur', 'suitable for': 'compatible',
    'wear gloves': 'gants', 'sports car': 'voiture de sport', 'running car': 'voiture de course',
    'jumping shrimp': 'crevette sauteuse', 'random col': 'couleur aléatoire', 'random color': 'couleur aléatoire',
    'sewn on eyes': 'yeux cousus', 'christmas tree': 'sapin de Noël', 'christmas elf star': 'étoile lutin de Noël',
    'santa claus': 'Père Noël', 'starry santa': 'Père Noël étoilé', 'gingerbread baby': 'bonhomme pain d’épice',
    'kids tree': 'sapin enfant', 'old man': 'vieil homme', 'buddha head': 'tête de Bouddha',
    'small fruit': 'petit fruit', 'new branch': 'nouvelle branche', 'four strings': '4 cordes',
    'horizontal rectangle': 'rectangle horizontal', 'vertical large': 'grand vertical',
    'body wave': 'ondulé', 'bob wig': 'perruque carrée', 'hair block': 'closure', 'lace intranet': 'lace',
    'basic payment set': 'lot modèle de base', 'induction style set': 'lot modèle à détection',
    'no aerial photography': 'sans photo aérienne', 'no light': 'sans lumière', 'no logo': 'sans logo',
    'pieces of red': 'pièces rouges', 'with a': 'avec un', 'ribbon': 'ruban', 'coating': 'revêtement',
    'framed': 'encadré', 'shaped': 'en forme', 'edge': 'bord', 'soft': 'doux',
    'middle zip': 'zip central', 'belt mesh': 'ceinture en maille', 'mesh': 'maille',
    # Mots simples
    'and': 'et', 'with': 'avec', 'without': 'sans', 'plus': '+', 'add': '+', 'for': 'pour', 'about': 'environ',
    'set': 'lot', 'suit': 'kit', 'package': 'pack', 'accessories': 'accessoires', 'style': 'modèle',
    'models': 'modèles', 'model': 'modèle', 'edition': 'édition', 'section': 'partie', 'pieces': 'pièces',
    'piece': 'pièce', 'small': 'petit', 'medium': 'moyen', 'large': 'grand', 'big': 'grand', 'single': 'simple',
    'short': 'court', 'plush': 'peluche', 'color': 'couleur', 'random': 'aléatoire', 'pillow': 'coussin',
    'mat': 'tapis', 'belt': 'ceinture', 'leash': 'laisse', 'bags': 'sacs', 'bag': 'sac', 'battery': 'batterie',
    'filter': 'filtre', 'cat': 'chat', 'dog': 'chien', 'paw': 'patte', 'print': 'imprimé', 'stickers': 'autocollants',
    'wood': 'bois', 'box': 'boîte', 'mirror': 'miroir', 'shell': 'coque', 'frame': 'cadre', 'base': 'socle',
    'light': 'lumière', 'lamp': 'lampe', 'card': 'carte', 'plug': 'prise', 'clip': 'pince', 'stone': 'pierre',
    'ball': 'balle', 'stick': 'bâton', 'fish': 'poisson', 'carp': 'carpe', 'clownfish': 'poisson-clown',
    'star': 'étoile', 'stars': 'étoiles', 'guitar': 'guitare', 'cherry': 'cerise', 'pumpkin': 'citrouille',
    'castle': 'château', 'floral': 'fleuri', 'stripe': 'rayures', 'snowman': 'bonhomme de neige', 'angel': 'ange',
    'elk': 'élan', 'mosaic': 'mosaïque', 'penguin': 'pingouin', 'tiger': 'tigre', 'hippopotamus': 'hippopotame',
    'wig': 'perruque', 'density': 'densité', 'english': 'anglais', 'german': 'allemand', 'french': 'français',
    'half': 'demi', 'full': 'complet', 'sticker': 'autocollant', 'armor': 'protection', 'square': 'carré',
    'foldable': 'pliable', 'rechargeable': 'rechargeable', 'cute': 'mignon', 'clouds': 'nuage', 'cloud': 'nuage',
    'silent': 'silencieux', 'gravity': 'gravité', 'leather': 'cuir', 'bracelet': 'bracelet', 'silvery': 'argenté',
    'ceramic': 'céramique', 'emerald': 'émeraude', 'chocolate': 'chocolat', 'olive': 'olive', 'crimson': 'cramoisi',
    'lilac': 'lilas', 'matcha': 'matcha', 'fluorescent': 'fluo', 'version': 'version', 'microphone': 'microphone',
    'spiral': 'spirale', 'baby': 'bébé', 'number': 'n°', 'size': 'taille', 'gloves': 'gants', 'christmas': 'Noël',
    'smart': 'connecté', 'dumb': 'simple', 'popularity': 'populaire', 'head': 'tête', 'gaming': 'gaming',
    'speaker': 'enceinte', 'cloth': 'chiffon', 'machine': 'machine', 'portable': 'portable', 'splicing': 'assemblé',
    'pot': 'pot', 'cup': 'gobelet', 'bowl': 'gamelle', 'pcs': 'pièces', 'pc': 'pièce',
}
for _en, _fr in COLORS:
    TERMS.setdefault(_en, _fr)
for _en, _fr in _SIMPLE_COLORS.items():
    for _mod, _adj in (('light', 'clair'), ('dark', 'foncé'), ('deep', 'foncé')):
        TERMS.setdefault(f'{_mod} {_en}', f'{_fr} {_adj}')

_TERM_RE = re.compile(
    rf'(?<![{_L}])(' + '|'.join(re.escape(k).replace(r'\ ', r'\s+') for k in sorted(TERMS, key=len, reverse=True))
    + rf')(?![{_L}])', re.IGNORECASE)

_NUMBER_WORDS = {'one': '1', 'two': '2', 'three': '3', 'four': '4', 'five': '5', 'six': '6',
                 'eight': '8', 'ten': '10', 'fifteen': '15'}

# Mots collés par CJ (« Set12 », « 19Style », « redset », « White2pcs »)
_GLUE_WORDS = 'set|style|size|baby|wave|wig|' + '|'.join(re.escape(c) for c in _SIMPLE_COLORS)
_GLUED = [
    (re.compile(rf'(?<![{_L}])({_GLUE_WORDS})(\d)', re.IGNORECASE), r'\1 \2'),
    (re.compile(rf'(\d)(style|pcs|pc|inches|inch|density|bags)(?![{_L}])', re.IGNORECASE), r'\1 \2'),
    (re.compile(rf'(?<![{_L}])({_GLUE_WORDS})(set|pcs)(?![{_L}])', re.IGNORECASE), r'\1 \2'),
    (re.compile(r'(?<![A-Za-z])(typec|apple|huawei)and(typec|apple|huawei)(?![A-Za-z])', re.IGNORECASE), r'\1 et \2'),
]

_NUMBERED = [
    (re.compile(rf'(?<![{_L}])lamp\s+(\d+)\s+piece\s+pack(?![{_L}])', re.IGNORECASE), r'lot de \1 lampes'),
    (re.compile(rf'(\d+)\s*(?:pcs|pc|pieces?)\.?(?![{_L}])', re.IGNORECASE),
     lambda m: f"{m.group(1)} pièce{'s' if m.group(1) != '1' else ''}"),
    (re.compile(rf'(\d+(?:\.\d+)?)(?:\s*(?:inches|inch)|in)(?![{_L}])', re.IGNORECASE), r'\1 pouces'),
    (re.compile(rf'(\d+)\s*style(?![{_L}])', re.IGNORECASE), r'modèle \1'),
    (re.compile(rf'(\d+)\s*number(?![{_L}])', re.IGNORECASE), r'n° \1'),
    (re.compile(r'(?<![A-Za-z])typec(?![A-Za-z])', re.IGNORECASE), 'Type-C'),
]

# Accord « couleur + nom » → « nom couleur » (« Black guitar » → « Guitare noire »)
_NOUNS_F = {'guitare', 'balle', 'carpe', 'pierre', 'ceinture', 'laisse', 'coque', 'boîte', 'étoile', 'lampe',
            'housse', 'pince', 'prise', 'carte', 'perruque', 'patte'}
_NOUNS_M = {'coussin', 'tapis', 'bâton', 'poisson', 'sac', 'cadre', 'miroir', 'lot', 'kit', 'socle', 'modèle', 'pack'}
_FEMININE = {'noir': 'noire', 'blanc': 'blanche', 'vert': 'verte', 'gris': 'grise', 'violet': 'violette',
             'doré': 'dorée', 'argenté': 'argentée', 'bleu': 'bleue'}
_FR_COLORS = set(_SIMPLE_COLORS.values()) | {'bordeaux', 'or'}


def _swap(text):
    words = text.split(' ')
    for i in range(len(words) - 1):
        color, noun = words[i].lower(), words[i + 1].lower()
        if color in _FR_COLORS and (noun in _NOUNS_F or noun in _NOUNS_M):
            adj = _FEMININE.get(color, color) if noun in _NOUNS_F else color
            words[i], words[i + 1] = words[i + 1].lower(), adj
            if i == 0:
                words[0] = words[0][0].upper() + words[0][1:]
    return ' '.join(words)


def translate_option(label):
    """Libellé d'option CJ en français, mot à mot avec les expressions connues"""
    if not label or not isinstance(label, str):
        return label
    text = re.sub(r'\s+', ' ', label).strip()
    for _ in range(2):  # « redset2pcs » : deux passes
        for pattern, repl in _GLUED:
            text = pattern.sub(repl, text)
    text = re.sub(rf'(?<![{_L}])with\s+({"|".join(_NUMBER_WORDS)})(?![{_L}])',
                  lambda m: 'with ' + _NUMBER_WORDS[m.group(1).lower()], text, flags=re.IGNORECASE)
    for pattern, repl in _NUMBERED:
        text = pattern.sub(repl, text)
    text = _TERM_RE.sub(lambda m: TERMS[re.sub(r'\s+', ' ', m.group(1).lower())], text)
    text = _swap(re.sub(r'\s+', ' ', text).strip(' .'))
    return text[:1].upper() + text[1:] if text else label


_SIZE_WORD = re.compile(r'^(\d?x{0,3}[sl]|xxs|xs|m|eu|us|uk|cm|mm|ml|pcs|pc)$', re.I)


def _french_vocab():
    words = set()
    for value in list(TERMS.values()) + list(_SIMPLE_COLORS.values()) + list(_FEMININE.values()):
        words.update(w.lower() for w in re.findall(rf'[{_L}’\']+', value))
    words |= _NOUNS_F | _NOUNS_M | _FR_COLORS | {'et', 'de', 'des', 'du', 'la', 'le', 'les', 'avec', 'sans', 'pour', 'en'}
    return words


_FR_VOCAB = None


def needs_translation(label):
    """Le traducteur local laisse-t-il des mots anglais (ou inconnus) dans ce libellé ?
    Sert à n'envoyer à DeepL que ce qu'il ne sait pas traduire."""
    global _FR_VOCAB
    if _FR_VOCAB is None:
        _FR_VOCAB = _french_vocab()
    if not label or not isinstance(label, str):
        return False
    if len([w for w in re.findall(rf'[{_L}]+', label) if len(w) >= 2]) >= 3:
        return True  # expression (« Coffee cup set ») : le mot à mot local ne suffit pas
    for word in re.findall(rf'[{_L}]+', translate_option(label)):
        w = word.lower()
        if len(w) >= 3 and w not in _FR_VOCAB and not _SIZE_WORD.match(w) and not word.isupper():
            return True
    return False
