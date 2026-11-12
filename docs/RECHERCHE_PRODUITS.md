# Recherche de produits

Admin MPS › **Recherche de produits** (`/admin/recherche-produits`) : trouver les meilleurs produits pour
un site (Sérénis, ALIAS, DIGITA, ou le catalogue MPS seul), par critères, et les comparer à ce qui se
vend sur le web. Rien n'est importé sans un clic, et toujours en brouillon.

## Une veille

- **Site** : où vont les produits importés (champ « Vitrines » du produit).
- **Recherches**, une par ligne : `Titre en français | mots tapés sur Amazon ou Google | recherche CJ en anglais | mots obligatoires`.
  Seul le titre est obligatoire ; « Faire compléter par Claude » remplit le reste (via INES). Les mots
  obligatoires (« lavalier|lapel, mic ») sont indispensables : sans eux, CJ renvoie ses best-sellers sans rapport.
  « Reprendre les recherches de la fiche du site » charge `scripts/vitrines/<code>.json`.
- **Critères CJ** : prix d'achat mini/maxi, photos, poids, stock, stock en France, nombre de produits retenus
  et de fiches lues par recherche.
- **Comparer au web** et **Relancer chaque lundi** (05h00 UTC, tâche `tasks.research_tasks.run_active_watches`).

## Un passage

1. CJ : les produits les plus listés par les boutiques CJ pour ces mots (product/listV2), filtrés sur les
   mots obligatoires, puis leur fiche avec les critères ; prix de vente de la grille habituelle.
2. Web, si DataForSEO est branché : Google Trends (intérêt moyen sur 12 mois en France), Amazon.fr
   (« acheté le mois dernier », note, prix) et Google Shopping (prix, avis). Produits notés sous 4/5 ignorés.
3. Verdicts : **Dispo chez CJ** (avec l'écart à notre prix et le prix médian du web), **À sourcer** (vu sur
   le web, rien de convenable chez CJ), **Repère du marché** (web, alors que CJ a déjà de quoi répondre).

Actions : **Importer en brouillon** (un produit déjà en ligne dans MPS reçoit seulement le site),
**Sourcing CJ** (demande envoyée à CJ, suivie dans Sourcing CJ), **Écarter** / **Reprendre**. Ces choix
restent d'un passage à l'autre. L'activation des brouillons se fait dans Boutiques et vitrines (contrôles
CJ, marge, fiche en français par Claude).

## Coût

- CJ : gratuit, une dizaine de requêtes par recherche sur les 50 000 points du jour.
- DataForSEO : environ 0,007 $ par recherche (Amazon 0,003 $, Shopping 0,002 $, Trends 0,011 $ pour 5).
  3 veilles de 15 recherches chaque lundi : moins de 1 $ par mois. Dépôt minimum 50 $, sans expiration.
- Claude (compléter les recherches) : quelques centimes, sur les crédits INES.

## Brancher DataForSEO

Compte sur dataforseo.com › API Access, puis dans INES › `/admin/integrations` :
`MULTIPROSHOP_DATAFORSEO_LOGIN` et `MULTIPROSHOP_DATAFORSEO_PASSWORD` (ou `DATAFORSEO_LOGIN` /
`DATAFORSEO_PASSWORD` dans `deploy/.env`), puis redémarrer web et worker. Sans eux, la recherche se fait
sur CJ seul et la note du passage le dit.

Code : `services/product_research.py`, `services/dataforseo.py`, `routes/admin_research.py`,
`models/product_research.py`. Test : `tests/scenarios/sc_research.py`.
