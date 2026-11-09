# Écosystème MultiProShop, INES et vitrines

*État au 08/11/2026 (soir).* Ce document décrit qui fait quoi entre INES, MultiProShop (MPS) et les sites de vente (TonyAlpha80, DIGITA, Sérénis), où se règle chaque chose et comment vérifier que tout fonctionne. L'historique des opérations faites en production (données modifiées, réglages, incidents) est dans [JOURNAL_EXPLOITATION.md](JOURNAL_EXPLOITATION.md).

## Qui fait quoi

| Brique | Rôle | Où |
|---|---|---|
| **INES** (ines.weballone.com) | Configuration et suivi : clés des fournisseurs, compte CJ unique, paiement Stripe, e-mails, moniteurs | `/opt/ines`, dépôt INES-organisation/INES |
| **MultiProShop** (multiproshop.com) | Gestion et vente : catalogue, prix, commandes, envoi des commandes chez CJ, e-mails clients | `/opt/multiproshop`, dépôt INES-organisation/multiproshop |
| **Vitrines** (tonyalpha80.com, serenis.multiproshop.com…) | Affichent une sélection du catalogue MPS. Le client paie et suit sa commande chez elles ; MPS encaisse et commande | Leur propre dépôt |

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
| `POST /payment-events` | jeton `PARTNER_TOKEN_INES` | Remboursement ou contestation Stripe transmis par le webhook Stripe d'INES : commande marquée remboursée, alerte (une contestation alerte aussi par e-mail) |

- **Jetons** : `PARTNER_TOKEN_<SITE>` dans `deploy/.env` de MPS, 24 caractères au minimum. La vitrine envoie le sien en `Authorization: Bearer …`.
- **Rattacher un produit à une vitrine** : admin MPS › fiche produit › champ « Vitrines (projets) », par exemple `tonyalpha, serenis`. La saisie est normalisée en minuscules et sans doublon.
- Sans `?project=`, une vitrine reçoit tout le catalogue publié. C'est le cas de TonyAlpha80 aujourd'hui.
- Les prix, le port et le montant à payer sont toujours recalculés par MPS, jamais repris de la vitrine.

## Vitrines de niche (Sérénis)

- `vitrine/app.py` est une petite boutique Flask qui affiche les produits d'un projet MPS et passe ses commandes par l'API partenaire. MPS reste le vendeur : prix, paiement, commande CJ, e-mails. Le pied de page le dit, et renvoie aux CGV et aux mentions légales de MPS.
- **Sérénis** : service `serenis-web` de `deploy/docker-compose.yml`, même image que MPS, sans ses secrets. Il est servi par ines-nginx sur `serenis.multiproshop.com`, dont le bloc est dans le nginx.conf d'INES.
  - Réglages dans `deploy/.env` de MPS : `PARTNER_TOKEN_SERENIS` (jeton de la vitrine) et `SERENIS_SECRET_KEY` (sessions).
  - Certificat : `sudo certbot certonly --webroot -w /opt/ines/certbot-webroot -d serenis.multiproshop.com --deploy-hook /opt/ines/scripts/certbot-custom-domain-hook.sh`.
  - Produits : champ « Vitrines (projets) » = `serenis` dans la fiche admin. La vitrine n'affiche que ceux-là, même par lien direct.
  - Accueil : produit mis en avant `VITRINE_HERO` (id MPS, 20987 par défaut), lots « rituels » `VITRINE_RITUALS` (JSON, sinon les trois lots par défaut de `vitrine/app.py`), délai annoncé `VITRINE_DELIVERY` (12-20). Un lot n'apparaît que si au moins deux de ses produits sont en ligne ; ses produits sont vendus à leur prix normal.
  - Livraison offerte : `FREE_SHIPPING_THRESHOLD_SERENIS` dans `deploy/.env` de MPS (39 € prévu). MPS ne l'offre que si la marge du panier reste positive.
  - Newsletter : même liste que MPS (source `serenis`) et même code -10 %, utilisable sur la vitrine. Codes promo acceptés au moment de la commande.
  - Avis : seulement ceux déposés par nos clients après livraison. Les avis CJ (laissés sur d'autres boutiques) ne sont jamais affichés.
  - Plan : une petite vitrine avant le Black Friday, puis en janvier le catalogue complet, avec ses lots « Rituel du soir ». Le document de départ est `LANCEMENT_MPS_NICHE_DROPSHIPPING.md` (docs INES, Business et croissance).
- **Une autre niche** : même service, copié avec d'autres `VITRINE_*` (projet, nom, slogan, couleur, adresse) et son propre jeton.

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

## Plusieurs fournisseurs

- Chaque produit a un **fournisseur** : admin MPS › fiche produit › champ « Fournisseur » (colonne `product.provider`, vide = CJ). Tous les produits actuels sont chez CJ.
- `services/providers.py` regroupe le panier par fournisseur :
  - **port** : chaque fournisseur donne ses tarifs. Un panier d'un seul fournisseur garde ses méthodes habituelles. Un panier mixte reçoit une seule méthode, qui additionne la moins chère de chaque fournisseur, avec un code du type `cj:CJPacket|bigbuy:GLS` ;
  - **commande** : après paiement, chaque fournisseur reçoit sa part. CJ ne reçoit que ses articles, avec sa propre méthode de livraison.
- Un fournisseur pas encore branché ne propose aucun port : ses produits ne peuvent pas être achetés. Si une commande payée en contient quand même, l'admin reçoit une alerte « Commande … à passer à la main ».
- **Brancher un fournisseur** (BigBuy, vidaXL…) : ajouter sa fonction de tarifs dans `QUOTERS` et sa fonction de commande dans `PLACERS`, de préférence en passant par un hub dans INES comme pour CJ.
  - Ses clés se saisissent dans INES › `/admin/integrations`, catégorie E-commerce : `VIDAXL_API_KEY`, `BIGBUY_API_KEY`, `SYNCEE_API_KEY`, `PRINTFUL_API_KEY`. Elles ne sont pas encore utilisées.
- À venir : le choix du fournisseur selon le pays de livraison. Les DOM sont hors du territoire TVA de l'UE : la livraison vers La Réunion est à vérifier chez chaque fournisseur européen, et CJ restera probablement le fournisseur pour la Réunion.
- Premier choix conseillé : BigBuy, qui a une API dropshipping, ou vidaXL, qui a des entrepôts aux Pays-Bas et en Pologne. Il faut d'abord ouvrir un compte chez eux.

## Contenu et pages

- **Fiches produits** : toutes en français, rédigées automatiquement à la publication. La fiche 1573, publiée à la main avant cette rédaction, a été réécrite le 08/11. Certaines photos CJ gardent du texte chinois.
- **Médiateur de la consommation** : CM2C (49 rue de Ponthieu, 75008 Paris, www.cm2c.net). Il est cité dans les mentions légales (section 7) et dans les CGV.
- **Mobile** : sous 576 px, l'en-tête se réduit quand on fait défiler la page vers le bas (de 138 à 57 px) et revient quand on remonte.

## Dépendances figées

- `constraints.txt` liste les versions exactes de l'image en production (Python 3.11). Le Dockerfile et la CI installent avec `pip install -r requirements.txt -c constraints.txt`.
- Pour mettre à jour un paquet : changer sa version dans `constraints.txt`, lancer les scénarios en Python 3.11, puis déployer.
- Pourquoi : le 05/11, une reconstruction a installé kombu 5.7, incompatible avec redis 5.0.1, et le worker Celery a tourné en boucle.

## Déploiement et vérifications

- **MPS** : `ssh ines-vps /opt/multiproshop/deploy/deploy.sh`. Le script :
  - sauvegarde la base, et s'arrête si la sauvegarde échoue ;
  - garde les journaux des conteneurs 30 jours dans `/home/ubuntu/multiproshop-logs`, car Docker les efface quand il recrée un conteneur ;
  - récupère `main`, puis reconstruit et redémarre.
  - Sauvegarde de nuit à 4 h 15 (`deploy/backup.sh`, cron du VPS).
- **INES** : `ssh ines-vps 'cd /opt/ines && ./scripts/deploy.sh'`. Le script lance aussi les migrations alembic.
- **Surveillance** : Uptime Kuma, avec alertes Telegram. La surveillance d'INES (table `uptime_checks`) est lancée par le cron du VPS toutes les 5 minutes. Ne pas retirer cette ligne : c'est son seul déclencheur.
- **Tests MPS** : `FLASK_ENV=testing python -m pytest tests/test_scenarios.py -q`. Chaque fichier `tests/scenarios/sc_*.py` est un parcours autonome.

## SEO

- `/sitemap.xml` contient les produits en ligne et seulement les catégories qui ont des produits. Il est mis en cache un jour. `/robots.txt` l'annonce.
- Search Console : la propriété Domaine est validée par l'enregistrement TXT `google-site-verification` chez OVH. Il faut le garder en place.
