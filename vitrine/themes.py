"""Thèmes des boutiques : identité (couleurs, polices, logo) et textes propres à chaque niche.

Le même code sert toutes les boutiques MPS (vitrine/app.py) ; seul le thème change, choisi par le
code du projet (VITRINE_PROJECT) ou forcé par VITRINE_THEME. Les réglages de l'admin MPS (nom,
slogan, couleur d'accent, produit mis en avant, lots, délai) passent toujours avant le thème.

Une nouvelle boutique = une entrée de THEMES. Ce qui n'y figure pas reprend BASE.
Les textes peuvent contenir {name} : il est remplacé par le nom de la boutique.
"""

FONTS_SERENIS = ('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;'
                 '9..144,600&family=Inter:wght@400;500;600&display=swap')

BASE = {
    # Identité visuelle (celle de Sérénis, qui sert de modèle)
    'name': 'Boutique',
    'tagline': 'Une sélection MultiProShop',
    'color': '#e0975a',
    'hero': '',
    'delivery': '12-20',
    'lots': [],
    'fonts_href': FONTS_SERENIS,
    'serif': '"Fraunces",Georgia,"Times New Roman",serif',
    'sans': '"Inter",system-ui,-apple-system,"Segoe UI",sans-serif',
    'palette': {
        'night': '#16213a', 'night-2': '#22325a', 'dawn-soft': '#f3d9bf', 'sand': '#f6f1e9', 'sand-2': '#efe7da',
        'ink': '#1f2433', 'muted': '#626a7d', 'card': '#fff', 'line': '#e6ddcf', 'ok': '#3f7d5a',
        'dawn-hover': '#d88845', 'glow': 'rgba(224,151,90,.9)', 'glow-soft': 'rgba(224,151,90,.45)',
        'header-bg': 'rgba(246,241,233,.92)', 'shadow-ink': 'rgba(22,33,58,.25)',
        'on-dark': '#d5d9e6', 'on-dark-2': '#c9cfdd', 'on-dark-3': '#dfe3ee', 'footer-text': '#aab2c5',
        'hero-bg': 'linear-gradient(180deg,#121b31 0%,#1c2a4c 45%,#3d3f63 72%,#b9775a 100%)',
        'hero-glow': 'rgba(243,190,135,.55)',
    },
    'radius': '18px',
    'btn_radius': '99px',
    'card_ratio': '1',          # proportions des photos des cartes : 1 (carré) ou 4/5 (portrait, mode)
    'hero_style': 'dark',       # dark : dégradé sombre, texte puis photo ; light : fond clair, photo puis texte
    'search': True,             # champ de recherche dans l'en-tête
    'topbar_extra': '',         # message ajouté au bandeau du haut
    'stars': False,
    # Logo : {color} = couleur d'accent, {night} = couleur sombre
    'logo': ('<svg width="34" height="34" viewBox="0 0 64 64" aria-hidden="true"><rect width="64" height="64" rx="16" '
             'fill="{night}"/><circle cx="32" cy="32" r="14" fill="{color}"/></svg>'),
    'favicon': ("<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'><rect width='64' height='64' rx='14' "
                "fill='{night}'/><circle cx='32' cy='32' r='14' fill='{color}'/></svg>"),

    # Textes
    'nav_lots': 'Sélections',
    'lots_anchor': 'selections',
    'lot_slug': 'selection',
    'lot_word': 'la sélection',
    'hero_eyebrow': 'Notre sélection',
    'hero_title': '{name}',
    'hero_lead': 'Des produits choisis un par un, livrés chez vous avec un numéro de suivi.',
    'hero_cta': 'Découvrir le produit vedette',
    'moments_title': 'Par où commencer',
    'lots_eyebrow': 'Nos sélections',
    'lots_title': "Tout ce qu'il faut, réuni pour vous",
    'lots_text': 'Des ensembles pensés pour aller bien ensemble. Vous choisissez les modèles, on ajoute tout au panier en une fois.',
    'lot_eyebrow': 'Sélection',
    'lot_button': 'Ajouter la sélection au panier',
    'lot_added': 'La sélection est dans votre panier',
    'lots_cta': 'Découvrir les sélections',
    'related_title': 'Complétez votre panier',
    'story': None,
    'newsletter_text': 'Recevez nos nouveautés et nos offres, une à deux fois par mois. Désinscription en un clic.',
    'footer_text': 'Une sélection de produits choisis pour vous.',
    'gift_note': '',
    'faq_extra': [],
    'product_extra': [],        # rubriques ajoutées à chaque fiche produit : [(titre, texte), …]
}

THEMES = {
    'serenis': {
        'name': 'Sérénis',
        'tagline': 'Le rituel du soir : sommeil, détente et cocooning',
        'hero': '20987',
        'stars': True,
        'lots': [
            {'name': 'Rituel du soir', 'text': 'Une lumière douce pour se lever, une brume légère et une lueur ambrée pour se coucher.',
             'ids': [20987, 20986, 21135]},
            {'name': 'Nuit étoilée', 'text': "Un ciel étoilé au plafond et une petite flamme pour s'endormir sans le noir complet.",
             'ids': [21093, 20955]},
            {'name': 'Cocon du dimanche', 'text': 'Plaid, coussin et couverture de sieste : tout pour ne plus quitter le canapé.',
             'ids': [20913, 20910, 20911]},
        ],
        'logo': ('<svg width="34" height="34" viewBox="0 0 64 64" aria-hidden="true"><rect width="64" height="64" rx="16" '
                 'fill="#16213a"/><circle cx="32" cy="42" r="15" fill="{color}"/><rect x="0" y="42" width="64" height="22" '
                 'fill="#16213a"/><path d="M12 44h40" stroke="#f6f1e9" stroke-width="3" stroke-linecap="round"/><path '
                 'd="M32 18v-6M16.5 24.5l-4-4M47.5 24.5l4-4" stroke="{color}" stroke-width="3" stroke-linecap="round"/></svg>'),
        'favicon': ("<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'><rect width='64' height='64' rx='14' "
                    "fill='#16213a'/><path d='M14 42a18 18 0 0 1 36 0z' fill='#e0975a'/><path d='M10 46h44' "
                    "stroke='#f6f1e9' stroke-width='3' stroke-linecap='round'/></svg>"),
        'nav_lots': 'Rituels',
        'lots_anchor': 'rituels',
        'lot_slug': 'rituel',
        'lot_word': 'le rituel',
        'hero_eyebrow': 'Se réveiller en douceur',
        'hero_title': 'Des soirs plus calmes, des matins plus doux.',
        'hero_lead': ('Une lumière qui monte comme un lever de soleil, un ciel étoilé au plafond, un plaid qui sent le '
                      'dimanche. {name} réunit les objets qui aident à ralentir.'),
        'hero_cta': 'Découvrir le réveil lumière',
        'moments_title': 'Trouvez votre façon de ralentir',
        'lots_eyebrow': 'Les rituels',
        'lot_eyebrow': 'Rituel',
        'lot_button': 'Ajouter le rituel au panier',
        'lot_added': 'Le rituel est dans votre panier',
        'lots_cta': 'Découvrir les rituels',
        'related_title': 'Complétez votre rituel',
        'story': {
            'eyebrow': 'Un soir {name}',
            'title': 'Trois gestes pour retrouver le calme',
            'text': ('Pas besoin de tout changer. Quelques habitudes simples suffisent souvent à rendre le coucher plus '
                     'doux et le réveil moins brutal.'),
            'steps': [
                ('Baisser la lumière', 'Une heure avant de dormir, remplacez le plafonnier par une lueur chaude : lampe de sel, veilleuse ou projecteur.'),
                ('Créer une ambiance', 'Une brume légère, un ciel étoilé, un plaid : le corps comprend que la journée est finie.'),
                ('Se réveiller avec la lumière', "Le réveil lumière éclaire peu à peu la chambre avant l'heure, comme un lever de soleil, même en plein hiver."),
            ],
        },
        'newsletter_text': 'Recevez nos idées de rituels, nos nouveautés et nos offres, une à deux fois par mois. Désinscription en un clic.',
        'footer_text': 'Des objets choisis pour ralentir le soir, mieux dormir et se réveiller en douceur.',
        'gift_note': 'Pour un cadeau de Noël, commandez avant la fin novembre.',
    },

    'horane': {
        'name': 'Horane',
        'tagline': 'La belle montre au prix honnête',
        'color': '#b8925a',
        'fonts_href': ('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700'
                       '&family=Inter:wght@400;500;600&display=swap'),
        'serif': '"Cormorant Garamond",Georgia,"Times New Roman",serif',
        'palette': {
            'night': '#141414', 'night-2': '#2a2723', 'dawn-soft': '#ecdcc2', 'sand': '#f7f4ee', 'sand-2': '#ece6db',
            'ink': '#1b1b1b', 'muted': '#66625c', 'card': '#fff', 'line': '#e3dccf', 'ok': '#3f7d5a',
            'dawn-hover': '#a37e47', 'glow': 'rgba(184,146,90,.85)', 'glow-soft': 'rgba(184,146,90,.4)',
            'header-bg': 'rgba(247,244,238,.92)', 'shadow-ink': 'rgba(20,20,20,.25)',
            'on-dark': '#d9d4cb', 'on-dark-2': '#cbc5ba', 'on-dark-3': '#e2ddd4', 'footer-text': '#a9a39a',
            'hero-bg': 'linear-gradient(160deg,#0f0f0f 0%,#1d1b19 55%,#3a3128 100%)',
            'hero-glow': 'rgba(212,175,110,.35)',
        },
        'radius': '6px',
        'btn_radius': '4px',
        'topbar_extra': 'Bracelets interchangeables',
        'product_extra': [
            ('Changer le bracelet', "Poussez la petite tige à attache rapide avec l'ongle, retirez le bracelet, enclenchez le "
             "nouveau. Vérifiez la largeur (18, 20 ou 22 mm) indiquée sur la fiche du bracelet."),
            ('Entretien', "Essuyez le boîtier avec un chiffon doux. Évitez le contact du bracelet cuir avec l'eau et le parfum."),
        ],
        'logo': ('<svg width="34" height="34" viewBox="0 0 64 64" aria-hidden="true"><rect width="64" height="64" rx="10" '
                 'fill="#141414"/><circle cx="32" cy="32" r="19" fill="none" stroke="{color}" stroke-width="3"/>'
                 '<path d="M32 32V19M32 32l9 5" stroke="#f7f4ee" stroke-width="3" stroke-linecap="round"/>'
                 '<circle cx="32" cy="32" r="2.6" fill="{color}"/></svg>'),
        'favicon': ("<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'><rect width='64' height='64' rx='10' "
                    "fill='#141414'/><circle cx='32' cy='32' r='19' fill='none' stroke='#b8925a' stroke-width='4'/>"
                    "<path d='M32 32V19M32 32l9 5' stroke='#f7f4ee' stroke-width='4' stroke-linecap='round'/></svg>"),
        'nav_lots': 'Coffrets',
        'lots_anchor': 'coffrets',
        'lot_slug': 'coffret',
        'lot_word': 'le coffret',
        'hero_eyebrow': 'Montres minimalistes · bracelets interchangeables',
        'hero_title': 'Une belle montre, sans payer la marque.',
        'hero_lead': ('Des cadrans sobres, des bracelets qui se changent en quelques secondes, des coffrets à offrir. '
                      '{name} vend ses montres au prix qu\'elles valent, et dit ce qu\'il y a dedans.'),
        'hero_cta': 'Découvrir la montre',
        'moments_title': 'Trouvez votre style',
        'lots_eyebrow': 'Les coffrets',
        'lots_title': 'Prêts à offrir',
        'lots_text': ('Une montre et ses bracelets, réunis pour aller ensemble. Vous choisissez les modèles, '
                      'on ajoute tout au panier en une fois.'),
        'lot_eyebrow': 'Coffret',
        'lot_button': 'Ajouter le coffret au panier',
        'lot_added': 'Le coffret est dans votre panier',
        'lots_cta': 'Découvrir les coffrets',
        'related_title': 'Pour aller avec',
        'story': {
            'eyebrow': 'Pourquoi {name}',
            'title': 'Le juste prix, expliqué',
            'text': ("Une montre n'a pas besoin de coûter 150 € pour être belle. Nous choisissons des modèles sobres, "
                     "nous décrivons honnêtement ce qu'ils sont et nous les vendons au prix qu'ils valent."),
            'steps': [
                ('Un cadran qui va avec tout', 'Des lignes simples, sans logo voyant : du jean au costume, la même montre suit.'),
                ('Un bracelet pour chaque jour', 'Les bracelets à attache rapide se changent en quelques secondes et sans outil : un cadran, plusieurs styles.'),
                ('Ce qui est écrit est vrai', 'Mouvement, matériaux, résistance à l\'eau : chaque fiche dit ce que la montre est, sans en rajouter.'),
            ],
        },
        'newsletter_text': 'Recevez nos nouveaux modèles, nos idées cadeaux et nos offres, une à deux fois par mois. Désinscription en un clic.',
        'footer_text': 'Des montres sobres et des bracelets interchangeables, vendus au prix qu\'ils valent.',
        'gift_note': 'Pour un cadeau, tenez compte de ce délai : pour la Saint-Valentin, commandez avant la fin janvier.',
        'faq_extra': [
            ('Ma montre est-elle étanche ?',
             "Nos montres résistent aux éclaboussures et à la pluie. Retirez-la pour vous doucher, nager ou plonger, "
             "quelle que soit l'indication gravée au dos."),
            ('Comment changer le bracelet ?',
             "La plupart de nos bracelets ont une attache rapide : poussez la petite tige sur le côté avec l'ongle, "
             "retirez le bracelet et enclenchez le nouveau. Chaque fiche indique la largeur (18, 20 ou 22 mm) : "
             "choisissez celle de votre montre."),
            ('Quelle garantie ?',
             "Comme tout achat en France, votre montre bénéficie de la garantie légale de conformité de deux ans. "
             "En cas de souci, écrivez-nous avec votre numéro de commande."),
        ],
    },

    'recovia': {
        'name': 'Recovia',
        'tagline': 'Récupération, posture et mobilité à la maison',
        'color': '#2bb38a',
        'fonts_href': 'https://fonts.googleapis.com/css2?family=Manrope:wght@500;600;700;800&family=Inter:wght@400;500;600&display=swap',
        'serif': '"Manrope",system-ui,sans-serif',
        'palette': {
            'night': '#1e2a33', 'night-2': '#2c3b47', 'dawn-soft': '#d4f1e6', 'sand': '#f5f8f7', 'sand-2': '#e8efed',
            'ink': '#1b2329', 'muted': '#5c6a73', 'card': '#fff', 'line': '#dbe4e1', 'ok': '#2f7d5a',
            'dawn-hover': '#21987a', 'glow': 'rgba(43,179,138,.75)', 'glow-soft': 'rgba(43,179,138,.35)',
            'header-bg': 'rgba(245,248,247,.92)', 'shadow-ink': 'rgba(30,42,51,.22)',
            'on-dark': '#cfdbe0', 'on-dark-2': '#c2d0d6', 'on-dark-3': '#dbe6ea', 'footer-text': '#9fb0b8',
            'hero-bg': 'linear-gradient(150deg,#16212a 0%,#1e2a33 50%,#24453f 100%)',
            'hero-glow': 'rgba(43,179,138,.35)',
        },
        'radius': '14px',
        'btn_radius': '12px',
        'hero_style': 'light',
        'topbar_extra': 'Sans appli, sans abonnement',
        'product_extra': [
            ("Précautions d'usage", "Produit de confort, pas un dispositif médical. Commencez doucement, n'appuyez jamais "
             "sur une zone douloureuse, une articulation ou un os. En cas de doute, de blessure ou de grossesse, "
             "demandez l'avis d'un professionnel de santé."),
        ],
        'logo': ('<svg width="34" height="34" viewBox="0 0 64 64" aria-hidden="true"><rect width="64" height="64" rx="14" '
                 'fill="{night}"/><path d="M14 38c8-14 14 6 22-8s10-6 14-4" fill="none" stroke="{color}" stroke-width="5" '
                 'stroke-linecap="round" stroke-linejoin="round"/><circle cx="46" cy="22" r="4" fill="#f5f8f7"/></svg>'),
        'favicon': ("<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'><rect width='64' height='64' rx='14' "
                    "fill='#1e2a33'/><path d='M14 38c8-14 14 6 22-8s10-6 14-4' fill='none' stroke='#2bb38a' "
                    "stroke-width='6' stroke-linecap='round'/></svg>"),
        'nav_lots': 'Kits',
        'lots_anchor': 'kits',
        'lot_slug': 'kit',
        'lot_word': 'le kit',
        'hero_eyebrow': 'Récupération · posture · mobilité',
        'hero_title': 'Ton corps te dit merci.',
        'hero_lead': ('Dix minutes de récupération après le sport, un dos mieux installé au bureau : {name} réunit le '
                      'matériel simple qui fait du bien, à utiliser chez soi.'),
        'hero_cta': 'Découvrir le produit',
        'moments_title': 'Que cherches-tu ?',
        'lots_eyebrow': 'Les kits',
        'lots_title': 'Tout pour ta routine',
        'lots_text': 'Des kits pensés pour aller ensemble. Tu choisis les modèles, on ajoute tout au panier en une fois.',
        'lot_eyebrow': 'Kit',
        'lot_button': 'Ajouter le kit au panier',
        'lot_added': 'Le kit est dans ton panier',
        'lots_cta': 'Découvrir les kits',
        'related_title': 'Pour compléter ta routine',
        'story': {
            'eyebrow': 'La routine {name}',
            'title': 'Trois habitudes, dix minutes par jour',
            'text': "Pas besoin d'une salle de sport. Quelques gestes réguliers suffisent souvent à se sentir moins raide et mieux installé.",
            'steps': [
                ('Bouger un peu, souvent', 'Deux minutes de mobilité toutes les heures, avec une bande ou une corde, valent mieux qu\'une longue séance par semaine.'),
                ('Relâcher après l\'effort', 'Rouleau, balle ou pistolet de massage : quelques minutes sur les muscles travaillés, sans forcer.'),
                ('Bien s\'installer', 'Un coussin lombaire et un écran à hauteur des yeux changent la journée de travail.'),
            ],
        },
        'newsletter_text': 'Reçois nos routines de 5 minutes, nos nouveautés et nos offres, une à deux fois par mois. Désinscription en un clic.',
        'footer_text': 'Du matériel simple pour récupérer, mieux se tenir et bouger, à la maison comme au bureau.',
        'gift_note': '',
        'faq_extra': [
            ('Ces produits soignent-ils les douleurs ?',
             "Non. Ce sont des produits de confort et de bien-être, pas des dispositifs médicaux. En cas de douleur "
             "persistante, de blessure ou de grossesse, demandez l'avis d'un professionnel de santé avant de les utiliser."),
            ('Quelle garantie ?',
             "Comme tout achat en France, vous bénéficiez de la garantie légale de conformité de deux ans. "
             "En cas de souci, écrivez-nous avec votre numéro de commande."),
        ],
    },

    'nuvoa': {
        'name': 'Nuvoa',
        'tagline': 'Le confort, en grand',
        'color': '#7a8450',
        'fonts_href': 'https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=Inter:wght@400;500;600&display=swap',
        'serif': '"DM Serif Display",Georgia,serif',
        'palette': {
            'night': '#2e2b26', 'night-2': '#3d3a33', 'dawn-soft': '#e5e6d2', 'sand': '#f6f2ea', 'sand-2': '#ebe4d6',
            'ink': '#2a2723', 'muted': '#6b665d', 'card': '#fffdf9', 'line': '#e3dccd', 'ok': '#5d7a45',
            'dawn-hover': '#66703f', 'glow': 'rgba(122,132,80,.7)', 'glow-soft': 'rgba(122,132,80,.35)',
            'header-bg': 'rgba(246,242,234,.92)', 'shadow-ink': 'rgba(46,43,38,.2)',
            'on-dark': '#ddd7cb', 'on-dark-2': '#cfc8ba', 'on-dark-3': '#e6e0d5', 'footer-text': '#aaa395',
            'hero-bg': 'linear-gradient(160deg,#2e2b26 0%,#4a4636 60%,#7a7552 100%)',
            'hero-glow': 'rgba(229,214,180,.35)',
        },
        'radius': '4px',
        'btn_radius': '2px',
        'card_ratio': '4/5',
        'hero_style': 'light',
        'topbar_extra': 'Guide des tailles sur chaque fiche',
        'product_extra': [
            ('Guide des tailles', "Coupe oversize : prenez votre taille habituelle pour le look des photos, une taille en "
             "dessous pour une coupe simplement décontractée. Les mesures à plat de chaque taille sont dans la "
             "description ; comparez-les avec un vêtement que vous aimez porter."),
            ('Entretien', "Lavage à 30 °C, à l'envers, sans sèche-linge, pour garder la forme et la couleur."),
        ],
        'logo': ('<svg width="34" height="34" viewBox="0 0 64 64" aria-hidden="true"><rect width="64" height="64" rx="8" '
                 'fill="{night}"/><path d="M16 26c0-8 32-8 32 0 6 0 6 12 0 12H16c-6 0-6-12 0-12z" fill="#f6f2ea"/>'
                 '<path d="M22 46h20" stroke="{color}" stroke-width="4" stroke-linecap="round"/></svg>'),
        'favicon': ("<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'><rect width='64' height='64' rx='8' "
                    "fill='#2e2b26'/><path d='M16 26c0-8 32-8 32 0 6 0 6 12 0 12H16c-6 0-6-12 0-12z' fill='#f6f2ea'/></svg>"),
        'nav_lots': 'Ensembles',
        'lots_anchor': 'ensembles',
        'lot_slug': 'ensemble',
        'lot_word': "l'ensemble",
        'hero_eyebrow': 'Oversize · loungewear · couleurs neutres',
        'hero_title': 'Le confort, en grand.',
        'hero_lead': ('Des coupes amples dans des tissus épais, en sable, olive et ardoise. Chez {name}, tout est '
                      'oversize : une coupe qui pardonne, et les mesures de chaque pièce sur sa fiche.'),
        'hero_cta': 'Découvrir la pièce',
        'moments_title': 'Trouvez votre pièce',
        'lots_eyebrow': 'Les ensembles',
        'lots_title': 'Assortis, prêts à porter',
        'lots_text': 'Des pièces qui vont ensemble. Vous choisissez tailles et couleurs, on ajoute tout au panier en une fois.',
        'lot_eyebrow': 'Ensemble',
        'lot_button': "Ajouter l'ensemble au panier",
        'lot_added': "L'ensemble est dans votre panier",
        'lots_cta': 'Découvrir les ensembles',
        'related_title': 'Pour aller avec',
        'story': {
            'eyebrow': 'Comment choisir sa taille',
            'title': 'Oversize, mais pas au hasard',
            'text': 'Une coupe ample pardonne beaucoup. Pour être sûr, comparez avec un vêtement que vous aimez porter.',
            'steps': [
                ('Prenez votre taille habituelle', "Pour le look des photos, gardez votre taille. Une taille en dessous donne une coupe simplement décontractée."),
                ('Comparez avec un vêtement à vous', 'Mesurez à plat la largeur et la longueur d\'un sweat que vous aimez, puis comparez avec le guide de la fiche.'),
                ('Regardez le mannequin', 'Chaque fiche indique sa taille et la taille portée, pour voir le tombé réel.'),
            ],
        },
        'newsletter_text': 'Recevez nos nouvelles pièces, nos idées de tenues et nos offres, une à deux fois par mois. Désinscription en un clic.',
        'footer_text': 'Des basiques amples et épais, aux couleurs neutres, pour être bien toute la journée.',
        'gift_note': '',
        'faq_extra': [
            ('Et si la taille ne va pas ?',
             "Vous avez 14 jours après réception pour nous retourner l'article, non porté et avec son étiquette. "
             "Écrivez-nous avec votre numéro de commande : nous vous indiquons la marche à suivre."),
            ('Comment laver mes vêtements ?',
             "À 30 °C, à l'envers, sans sèche-linge : c'est ce qui garde le mieux la forme et la couleur. "
             "Les consignes exactes sont sur l'étiquette de chaque pièce."),
        ],
    },

    'patto': {
        'name': 'Patto',
        'tagline': 'Des accessoires malins pour chats heureux',
        'color': '#c8643b',
        'fonts_href': 'https://fonts.googleapis.com/css2?family=Fredoka:wght@500;600;700&family=Inter:wght@400;500;600&display=swap',
        'serif': '"Fredoka",system-ui,sans-serif',
        'palette': {
            'night': '#3b3a35', 'night-2': '#4b4a44', 'dawn-soft': '#f6dccd', 'sand': '#fbf6ee', 'sand-2': '#f1e9dc',
            'ink': '#2d2c28', 'muted': '#6c6a62', 'card': '#fff', 'line': '#eadfce', 'ok': '#6f8f6a',
            'dawn-hover': '#b0552f', 'glow': 'rgba(200,100,59,.7)', 'glow-soft': 'rgba(200,100,59,.35)',
            'header-bg': 'rgba(251,246,238,.92)', 'shadow-ink': 'rgba(59,58,53,.2)',
            'on-dark': '#e2ddd3', 'on-dark-2': '#d6d0c4', 'on-dark-3': '#ebe6dd', 'footer-text': '#b2ac9f',
            'hero-bg': 'linear-gradient(160deg,#3b3a35 0%,#55604f 60%,#8fa58a 100%)',
            'hero-glow': 'rgba(246,220,205,.4)',
        },
        'radius': '22px',
        'hero_style': 'light',
        'topbar_extra': 'Pensé pour les chats',
        'product_extra': [
            ('Sécurité', "Surveillez votre animal quand il découvre un nouvel accessoire. Rangez les jouets à plumes ou à "
             "ficelle après le jeu et remplacez un jouet abîmé."),
        ],
        'logo': ('<svg width="34" height="34" viewBox="0 0 64 64" aria-hidden="true"><rect width="64" height="64" rx="18" '
                 'fill="{color}"/><circle cx="32" cy="40" r="10" fill="#fbf6ee"/><circle cx="19" cy="27" r="5" fill="#fbf6ee"/>'
                 '<circle cx="27" cy="19" r="5" fill="#fbf6ee"/><circle cx="37" cy="19" r="5" fill="#fbf6ee"/>'
                 '<circle cx="45" cy="27" r="5" fill="#fbf6ee"/></svg>'),
        'favicon': ("<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'><rect width='64' height='64' rx='18' "
                    "fill='#c8643b'/><circle cx='32' cy='40' r='10' fill='#fbf6ee'/><circle cx='19' cy='27' r='5' fill='#fbf6ee'/>"
                    "<circle cx='27' cy='19' r='5' fill='#fbf6ee'/><circle cx='37' cy='19' r='5' fill='#fbf6ee'/>"
                    "<circle cx='45' cy='27' r='5' fill='#fbf6ee'/></svg>"),
        'nav_lots': 'Kits',
        'lots_anchor': 'kits',
        'lot_slug': 'kit',
        'lot_word': 'le kit',
        'hero_eyebrow': 'Pour les chats (et leurs humains)',
        'hero_title': 'Un chat heureux, un canapé intact.',
        'hero_lead': ('Une fontaine qui donne envie de boire, un griffoir plus tentant que le canapé, une brosse qui '
                      'retient les poils : {name} choisit des accessoires beaux et qui règlent de vrais petits problèmes.'),
        'hero_cta': 'Découvrir le produit',
        'moments_title': 'Par quoi commencer',
        'lots_eyebrow': 'Les kits',
        'lots_title': 'Bien équipé dès le premier jour',
        'lots_text': 'Des kits pensés pour aller ensemble. Vous choisissez les modèles, on ajoute tout au panier en une fois.',
        'lot_eyebrow': 'Kit',
        'lot_button': 'Ajouter le kit au panier',
        'lot_added': 'Le kit est dans votre panier',
        'lots_cta': 'Découvrir les kits',
        'related_title': 'Il va aussi adorer',
        'story': {
            'eyebrow': 'Les conseils {name}',
            'title': 'Trois petites choses qui changent tout',
            'text': 'Un chat a des besoins simples. Les satisfaire évite souvent les griffes sur le canapé et les poils partout.',
            'steps': [
                ("Lui donner envie de boire", "Beaucoup de chats préfèrent l'eau qui bouge : une fontaine, avec un filtre changé chaque mois."),
                ('Lui offrir un endroit à griffer', 'Placé près de son coin préféré, un griffoir devient plus tentant que le canapé.'),
                ('Le brosser un peu, souvent', 'Deux minutes par jour en période de mue, et beaucoup moins de poils dans la maison.'),
            ],
        },
        'newsletter_text': 'Recevez nos conseils, nos nouveautés et un rappel quand il faut changer le filtre de la fontaine. Désinscription en un clic.',
        'footer_text': 'Des accessoires beaux et malins, choisis pour la vie de tous les jours avec un chat.',
        'gift_note': '',
        'faq_extra': [
            ('Ces jouets sont-ils sans danger ?',
             "Nous évitons les petites pièces qui se détachent. Surveillez toujours votre animal quand il joue, et "
             "rangez les jouets à plumes ou à ficelle après la séance."),
        ],
    },

    'odysa': {
        'name': 'Odysa',
        'tagline': 'Voyager en cabine, malin',
        'color': '#c96b4b',
        'fonts_href': 'https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&family=Inter:wght@400;500;600&display=swap',
        'palette': {
            'night': '#1c2b44', 'night-2': '#273a5a', 'dawn-soft': '#f4d6c8', 'sand': '#f7f1e6', 'sand-2': '#ede3d2',
            'ink': '#1d2433', 'muted': '#5f6878', 'card': '#fff', 'line': '#e5dac7', 'ok': '#3f7d5a',
            'dawn-hover': '#b25a3c', 'glow': 'rgba(201,107,75,.75)', 'glow-soft': 'rgba(201,107,75,.38)',
            'header-bg': 'rgba(247,241,230,.92)', 'shadow-ink': 'rgba(28,43,68,.22)',
            'on-dark': '#d4dae6', 'on-dark-2': '#c6cedd', 'on-dark-3': '#dde3ee', 'footer-text': '#a7b1c4',
            'hero-bg': 'linear-gradient(170deg,#14223a 0%,#1c2b44 50%,#2f5b7a 85%,#c99a6b 100%)',
            'hero-glow': 'rgba(244,214,200,.4)',
        },
        'radius': '14px',
        'btn_radius': '10px',
        'topbar_extra': 'Pensé pour le bagage cabine',
        'product_extra': [
            ('Dimensions et cabine', "Les dimensions exactes sont dans la description. Les règles de bagage cabine "
             "changent d'une compagnie à l'autre : vérifiez-les avant le départ."),
        ],
        'logo': ('<svg width="34" height="34" viewBox="0 0 64 64" aria-hidden="true"><rect width="64" height="64" rx="14" '
                 'fill="{night}"/><rect x="20" y="20" width="24" height="30" rx="5" fill="none" stroke="#f7f1e6" '
                 'stroke-width="3.5"/><path d="M27 20v-5h10v5" fill="none" stroke="#f7f1e6" stroke-width="3.5"/>'
                 '<path d="M20 34h24" stroke="{color}" stroke-width="3.5"/></svg>'),
        'favicon': ("<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'><rect width='64' height='64' rx='14' "
                    "fill='#1c2b44'/><rect x='20' y='20' width='24' height='30' rx='5' fill='none' stroke='#f7f1e6' "
                    "stroke-width='4'/><path d='M20 34h24' stroke='#c96b4b' stroke-width='4'/></svg>"),
        'nav_lots': 'Kits',
        'lots_anchor': 'kits',
        'lot_slug': 'kit',
        'lot_word': 'le kit',
        'hero_eyebrow': 'Organisation cabine · confort en vol',
        'hero_title': 'Tout en cabine. Zéro frais de bagage.',
        'hero_lead': ('Des cubes qui rangent, des sacs qui compressent, un oreiller qui tient le cou : {name} réunit '
                      'ce qui permet de partir une semaine avec un seul bagage cabine.'),
        'hero_cta': 'Découvrir le produit',
        'moments_title': 'Préparez votre départ',
        'lots_eyebrow': 'Les kits',
        'lots_title': 'Prêts pour le départ',
        'lots_text': 'Des kits pensés pour aller ensemble. Vous choisissez les modèles, on ajoute tout au panier en une fois.',
        'lot_eyebrow': 'Kit',
        'lot_button': 'Ajouter le kit au panier',
        'lot_added': 'Le kit est dans votre panier',
        'lots_cta': 'Découvrir les kits',
        'related_title': 'À glisser dans la valise',
        'story': {
            'eyebrow': 'La méthode {name}',
            'title': 'Une semaine dans un bagage cabine',
            'text': "Ce n'est pas une question de taille de valise, mais de rangement.",
            'steps': [
                ('Un cube par usage', 'Hauts, bas, sous-vêtements : chaque cube a sa place et se retrouve sans tout vider.'),
                ('Compresser le volumineux', 'Pulls et vestes prennent deux fois moins de place dans un sac de compression.'),
                ("Garder l'essentiel à portée", 'Papiers, câbles et trousse de toilette dans des pochettes faciles à sortir au contrôle.'),
            ],
        },
        'newsletter_text': 'Recevez notre liste de bagage cabine, nos astuces et nos offres, une à deux fois par mois. Désinscription en un clic.',
        'footer_text': 'Des accessoires légers pour voyager en cabine, mieux rangé et plus serein.',
        'gift_note': 'Pour un départ en vacances, tenez compte de ce délai et commandez au moins trois semaines avant.',
        'faq_extra': [
            ('Vos produits respectent-ils les dimensions cabine ?',
             "Les cubes et pochettes se glissent dans tous les bagages cabine. Les dimensions exactes sont sur chaque "
             "fiche : vérifiez celles autorisées par votre compagnie, elles changent de l'une à l'autre."),
        ],
    },
}


def theme_for(code):
    """Thème complet d'un projet : BASE, complété par son entrée de THEMES (palette fusionnée)"""
    own = THEMES.get((code or '').lower(), {})
    theme = {**BASE, **own}
    theme['palette'] = {**BASE['palette'], **own.get('palette', {})}
    return theme
