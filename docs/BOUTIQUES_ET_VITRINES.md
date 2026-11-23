# Boutiques et vitrines MPS

*Mis à jour le 23/11/2026.* Comment créer, gérer et publier les sites qui vendent le catalogue MultiProShop. Le schéma d'ensemble (INES, CJ, Stripe) est dans [ECOSYSTEME.md](ECOSYSTEME.md).

## Deux formes, un seul vendeur

| | Boutique | Vitrine |
|---|---|---|
| C'est | un site de vente à sa marque, dont c'est le métier | la rubrique produits d'un site dont ce n'est pas le métier |
| Exemples | Sérénis (serenis.multiproshop.com) | ALIAS, le Magasin de tonyalpha80.com ; DIGITA, le matériel recommandé de digita.buzz |
| Code | `vitrine/app.py` et son thème dans `vitrine/themes.py`, servi par MPS (conteneur `<code>-web`) | le site lui-même (son dépôt), qui lit l'API partenaire |
| Produits | ceux marqués de son code | ceux marqués de son code |
| Panier et paiement | sur la boutique, via l'API partenaire | sur le site (TA80) ou par un lien vers la fiche MPS (DIGITA, au départ) |

Dans les deux cas, MPS reste le vendeur : il recalcule les prix et le port, encaisse avec le Stripe d'INES, passe la commande chez CJ par le hub d'INES et envoie les e-mails. Les CGV et mentions légales sont celles de MPS.

## Thèmes des boutiques

Toutes les boutiques partagent le même code (`vitrine/app.py`, `vitrine/templates/`). Ce qui les distingue est dans **`vitrine/themes.py`**, une entrée par code de boutique :

- **identité** : palette (fond, couleur sombre, accent, dégradé de l'accueil), polices Google, arrondis des cartes et des boutons, logo et favicon en SVG, proportions des photos (carré, ou 4/5 pour la mode) ;
- **mise en page** : accueil sombre (texte puis photo) ou clair (photo puis texte) ;
- **textes** : accroche, bouton principal, nom des lots (rituels, coffrets, kits, ensembles) et leur adresse (`/coffret/1`…), section « Pourquoi nous » en trois étapes, newsletter, pied de page, questions fréquentes en plus, rubriques en plus sur chaque fiche (guide des tailles, entretien, précautions), message du bandeau du haut.

Le thème est choisi par `VITRINE_PROJECT` (ou forcé par `VITRINE_THEME`). Les réglages de l'admin (nom, slogan, couleur d'accent, produit vedette, lots, délai) passent toujours avant. Un code sans thème prend `BASE`, une version neutre de Sérénis. Les textes acceptent `{name}`, remplacé par le nom de la boutique.

Ce que chaque boutique a, quel que soit son thème : recherche dans l'en-tête, menu mobile, bandeau de réassurance, collections en vignettes, lots ajoutés au panier en une fois, date de livraison estimée sur la fiche, barre d'achat fixe sur mobile, jauge de livraison offerte dans le panier, « Vus récemment » (gardé dans le navigateur du client), avis vérifiés uniquement, données produit structurées pour Google.

`tests/test_vitrine_themes.py` rend les pages de chaque thème et vérifie qu'aucun texte d'une autre boutique n'y apparaît.

## Boutiques en préparation (docs INES › FACTION › MPS)

| Code | Niche | Lancement prévu par les docs | Thème | Fiche de recherche CJ |
|---|---|---|---|---|
| `horane` | montres minimalistes, bracelets interchangeables | mi-janvier 2027 (Saint-Valentin) | noir, or, crème ; coffrets | `scripts/vitrines/horane.json` |
| `recovia` | récupération, posture, mobilité | 2-5 janvier 2027 (résolutions) | ardoise, menthe ; kits | `scripts/vitrines/recovia.json` |
| `nuvoa` | oversize et loungewear | février-mars 2027 | crème, olive, sable ; ensembles ; photos 4/5 | `scripts/vitrines/nuvoa.json` |
| `patto` | accessoires chat | avril-mai 2027 | crème, terracotta, sauge ; kits | `scripts/vitrines/patto.json` |
| `odysa` | voyage en cabine | mai 2027 | bleu nuit, sable, terracotta ; kits | `scripts/vitrines/odysa.json` |

Les noms sont provisoires (vérification INPI/EUIPO à faire) : changer de nom avant la création de la boutique dans l'admin, car le code est définitif.

Les fiches de recherche peuvent lever une exclusion de la liste de MPS avec `"autorises"` (ex. « massage gun » pour Recovia, « food bowl » pour Patto).

## Où tout se gère

**Admin MPS › Boutiques et vitrines** (`/admin/vitrines`, table `storefront`) :

- **la liste** : type, état, produits en ligne et en brouillon, commandes et chiffre d'affaires des 30 derniers jours, seuil de livraison offerte, nombre d'étapes de branchement restantes ;
- **la fiche** de chaque site :
  - réglages : nom, adresse, état, slogan, couleur, produit mis en avant, délai annoncé, seuil de livraison offerte, lots de l'accueil (boutiques), préfixe INES, notes. Une boutique les relit toutes les 5 minutes (`GET /api/partner/storefront/<code>`) ; les variables `VITRINE_*` ne servent plus que de secours ;
  - produits : recherche dans le catalogue MPS, ajout par cases ou par numéros, retrait, publication des brouillons d'un coup, dépublication ;
  - mise en ligne : les étapes, cochées quand MPS peut les vérifier (produits en ligne, jeton présent).
- **États** : « En préparation » (rien ne change pour le site), « En ligne », « En pause » (le catalogue du site renvoie zéro produit, rien n'est effacé, les autres sites continuent).

Ce qui reste hors de l'admin, exprès : les **jetons** (`PARTNER_TOKEN_<CODE>`) et clés de session, dans `deploy/.env` du VPS. Ce sont des secrets.

Deux règles à connaître :

- **Publier** un produit le met en ligne sur MultiProShop et sur tous les sites qui le portent. Pour le sortir d'un seul site, utiliser « Retirer de la vitrine ».
- La **mention des commandes** (« Commande passée sur … ») est fixée à la création. Elle sert à retrouver les ventes de chaque site, dans la liste comme dans les chiffres d'INES : elle ne se modifie pas.

## Créer une boutique ou une vitrine

1. **Admin › Boutiques et vitrines › Nouvelle** : type, nom, code (minuscules, définitif), adresse. Elle démarre « en préparation ».
2. **Choisir les produits**, de deux façons :
   - **déjà dans MPS** : recherche dans la fiche, cases à cocher, « Ajouter » ;
   - **nouveaux, depuis CJ** : écrire une fiche de mots-clés `scripts/vitrines/<code>.json` (groupes, recherches en anglais, nom français, motifs pour retrouver l'existant), puis sur le VPS :
     ```
     docker exec multiproshop-web python scripts/select_vitrine_products.py scripts/vitrines/<code>.json
     docker exec multiproshop-web python scripts/import_selection.py instance/vitrine_<code>.json --project <code> --draft --dry-run
     docker exec multiproshop-web python scripts/import_selection.py instance/vitrine_<code>.json --project <code> --draft
     ```
     La sélection est en lecture seule. Elle classe les produits CJ par nombre de boutiques qui les vendent, contrôle photos, poids et stock, et calcule le prix avec la grille MPS (coût × 2,5 sous 10 €, × 2 sous 30 €, × 1,6 au-delà, arrondi à x,90 €). L'import crée des brouillons rattachés au site ; un produit déjà dans MPS reçoit seulement le code, sa fiche n'est pas réécrite.
3. **Relire les brouillons** (titre, photos, prix), puis « Publier les brouillons ».
4. **Brancher le site** (étapes affichées dans sa fiche) :
   - jeton : `python3 -c "import secrets;print(secrets.token_urlsafe(32))"`, dans `/opt/multiproshop/deploy/.env` sous `PARTNER_TOKEN_<CODE>`, puis `deploy.sh` ;
   - **boutique** : copier le bloc `serenis-web` de `deploy/docker-compose.yml` (`VITRINE_PROJECT`, `VITRINE_TOKEN`, `SECRET_KEY`), enregistrement DNS, bloc nginx dans le nginx.conf d'INES, certificat certbot ;
   - **vitrine** : le site appelle `/api/partner/catalogue?project=<code>` et envoie le jeton pour le port et les commandes. Le jeton se range dans INES › `/admin/integrations` sous `<PREFIXE>MPS_PARTNER_TOKEN`.
5. **Passer l'état à « En ligne »**.

## Connexion à INES (comme Sérénis)

| Ce qu'apporte INES | Branchement | Pour un nouveau site |
|---|---|---|
| Paiement Stripe | MPS crée la session de paiement chez INES | rien à faire |
| Commandes CJ, suivi, stock | hub CJ d'INES, un seul compte | rien à faire |
| E-mails clients | envoyés par MPS au nom du site (expéditeur INES) | rien à faire |
| Remboursements et contestations Stripe | webhook Stripe d'INES → `POST /api/partner/payment-events` | rien à faire |
| Chiffres dans `/ecommerce › Boutiques connectées` | INES lit `/api/partner/stats`, qui compte chaque site à part dès que son jeton existe | le jeton |
| Newsletter | même liste que MPS, source = le code du site, recopiée dans INES | rien à faire |
| Prospects et clients dans le CRM | le site les envoie à INES avec sa propre clé (`INES_API_KEY`) | sur le site (TA80 et DIGITA le font déjà) |

## État au 12/11/2026

| Site | Type | État | Produits | Branchement |
|---|---|---|---|---|
| Sérénis | boutique | en ligne | 19 | complet |
| ALIAS (tonyalpha) | vitrine | en préparation | sélection en brouillon | le Magasin lit aujourd'hui tout le catalogue : passer `project=tonyalpha` à l'API |
| DIGITA | vitrine | en préparation | sélection en brouillon | pas encore de jeton ; la boutique renvoie vers multiproshop.com |
