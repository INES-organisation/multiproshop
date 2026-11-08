# Écosystème MultiProShop, INES et vitrines

*État au 08/11/2026.* Ce document décrit qui fait quoi entre INES, MultiProShop (MPS) et les sites de vente (TonyAlpha80, DIGITA, Sérénis), où se règle chaque chose et comment vérifier que tout fonctionne. L'historique des opérations faites en production (données modifiées, réglages, incidents) est dans [JOURNAL_EXPLOITATION.md](JOURNAL_EXPLOITATION.md).

## Qui fait quoi

| Brique | Rôle | Où |
|---|---|---|
| **INES** (ines.weballone.com) | Configuration et suivi : clés des fournisseurs, compte CJ unique, paiement Stripe, e-mails, moniteurs | `/opt/ines`, dépôt INES-organisation/INES |
| **MultiProShop** (multiproshop.com) | Gestion et vente : catalogue, prix, commandes, envoi des commandes chez CJ, e-mails clients | `/opt/multiproshop`, dépôt INES-organisation/multiproshop |
| **Vitrines** (tonyalpha80.com…) | Affichent une sélection du catalogue MPS. Le client paie et suit sa commande chez elles ; MPS encaisse et commande | Leur propre dépôt |

Les trois tournent sur le même VPS (`ssh ines-vps`).

## Fournisseur CJ : un seul compte, via INES

- Les identifiants CJ sont dans INES › `/admin/integrations` : `CJ_API_KEY` (et `CJ_EMAIL`, `CJ_DEV_KEY`). À défaut, INES reprend `MULTIPROSHOP_CJ_*`.
- CJ n'autorise qu'une authentification toutes les 5 minutes et un appel par seconde par compte. INES partage donc un seul jeton (Redis `cjhub:token`) et une file d'attente commune entre toutes les boutiques.
- MPS passe par INES quand `CJ_VIA_INES=1` dans `deploy/.env`. C'est le cas en production.
- Webhooks : CJ envoie tout à INES (`/api/v1/external/cj/webhook?token=…`). INES renvoie à la boutique qui a créé la commande les événements de commande, et à toutes les boutiques les événements produit et stock.
  - L'adresse de renvoi de chaque boutique est `<PREFIXE>CJ_FORWARD_URL` dans INES, et son jeton `<PREFIXE>CJ_FORWARD_TOKEN`, envoyé dans l'en-tête `X-CJ-Webhook-Token`.
- Contrôle : `GET /api/v1/external/cj/status` sur INES, avec une clé API d'un compte admin.

## Vitrines : l'API partenaires de MPS

Toutes les routes sont sous `/api/partner`.

| Route | Accès | Usage |
|---|---|---|
| `GET /catalogue` | public, CORS ouvert | Produits publiés. `?project=<vitrine>` limite aux produits marqués pour cette vitrine. Autres paramètres : `q`, `category`, `sort`, `page`, `per_page` |
| `GET /products/<id>` | public | Fiche avec ses variantes |
| `POST /shipping`, `POST /orders`, `POST /orders/confirm`, `GET /orders` | jeton de la vitrine | Livraison, commande et paiement, suivi client |
| `GET /stats` | jeton `PARTNER_TOKEN_INES` | Chiffres pour les moniteurs d'INES |

- **Jetons** : `PARTNER_TOKEN_<SITE>` dans `deploy/.env` de MPS, 24 caractères au minimum. La vitrine envoie le sien en `Authorization: Bearer …`.
- **Rattacher un produit à une vitrine** : admin MPS › fiche produit › champ « Vitrines (projets) », par exemple `tonyalpha, serenis`. La saisie est normalisée en minuscules et sans doublon.
- Sans `?project=`, une vitrine reçoit tout le catalogue publié. C'est le cas de TonyAlpha80 aujourd'hui.
- Les prix, le port et le montant à payer sont toujours recalculés par MPS, jamais repris de la vitrine.

## Chiffres de MPS dans les moniteurs d'INES

- MPS expose `GET /api/partner/stats` :
  - ventes, chiffre d'affaires et marge sur 1, 7 et 30 jours ;
  - commandes payées par site ;
  - commandes payées pas encore passées chez CJ ;
  - colis en route ;
  - produits en ligne et en rupture ;
  - date de la dernière synchro CJ.
- INES les lit sur `GET /api/v1/moniteurs/boutiques` (admins seulement) et les affiche dans **/ecommerce › Boutiques connectées**.
- Réglages côté INES (`/admin/integrations`) : `MULTIPROSHOP_STATS_URL` (adresse de `/api/partner/stats`) et `MULTIPROSHOP_STATS_TOKEN`, de même valeur que `PARTNER_TOKEN_INES` côté MPS.
- Une autre boutique se branche de la même façon : `<PREFIXE>STATS_URL` et `<PREFIXE>STATS_TOKEN`, avec les préfixes `TONYALPHA_`, `DIGITA_` et `SERENIS_`.

## Sourcing CJ (produits AliExpress, 1688, Taobao…)

Admin MPS › **Sourcing CJ** (`/admin/cj-sourcing`) : lien du produit, nom, adresse de la photo, prix cible facultatif. MPS envoie la demande à CJ (`product/sourcing/create`, via le hub INES). « Actualiser » relit l'état des demandes en cours (`product/sourcing/queryList`, un appel par demande, 20 au plus). Une fois le produit trouvé, il s'importe en brouillon avec la catégorie choisie, comme depuis « Rechercher sur CJ ». CJ ne documente que les états 3 (trouvé) et 5 (échec) : toute autre valeur est affichée comme en cours, avec le libellé de CJ.

## Autres fournisseurs (à venir)

Les fiches vidaXL/dropXL, BigBuy, Syncee et Printful sont dans INES › `/admin/integrations`, catégorie E-commerce, pour y saisir les clés. **Elles ne sont pas encore utilisées.** Il faut d'abord que les commandes MPS ne dépendent plus d'un seul fournisseur (produit → fournisseur, port par fournisseur, panier qui mélange plusieurs fournisseurs), puis étendre le hub CJ d'INES à un hub de fournisseurs, sur le même principe.

Premier choix : vidaXL, qui a des entrepôts aux Pays-Bas et en Pologne, une API et peu de recouvrement avec CJ. Les DOM sont hors du territoire TVA de l'UE : la livraison vers La Réunion est à vérifier chez chaque fournisseur, et CJ restera probablement le fournisseur pour la Réunion.

## Dépendances figées

- `constraints.txt` liste les versions exactes de l'image en production (Python 3.11). Le Dockerfile et la CI installent avec `pip install -r requirements.txt -c constraints.txt`.
- Pour mettre à jour un paquet : changer sa version dans `constraints.txt`, lancer les scénarios en Python 3.11, puis déployer.
- Pourquoi : le 05/11, une reconstruction a installé kombu 5.7, incompatible avec redis 5.0.1, et le worker Celery a tourné en boucle.

## Déploiement et vérifications

- **MPS** : `ssh ines-vps 'cd /opt/multiproshop && git pull --ff-only origin main && docker compose -f deploy/docker-compose.yml --env-file deploy/.env up -d --build'`.
  - Sauvegarde de nuit à 4 h 15 (`deploy/backup.sh`, cron du VPS). Faire une sauvegarde manuelle avant chaque déploiement.
- **INES** : `ssh ines-vps 'cd /opt/ines && ./scripts/deploy.sh'`. Le script lance aussi les migrations alembic.
- **Surveillance** : Uptime Kuma, avec alertes Telegram. La surveillance d'INES (table `uptime_checks`) est lancée par le cron du VPS toutes les 5 minutes. Ne pas retirer cette ligne : c'est son seul déclencheur.
- **Tests MPS** : `FLASK_ENV=testing python -m pytest tests/test_scenarios.py -q`. Chaque fichier `tests/scenarios/sc_*.py` est un parcours autonome.

## SEO

- `/sitemap.xml` contient les produits en ligne et seulement les catégories qui ont des produits. Il est mis en cache un jour. `/robots.txt` l'annonce.
- Search Console : la propriété Domaine est validée par l'enregistrement TXT `google-site-verification` chez OVH. Il faut le garder en place.
