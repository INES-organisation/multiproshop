# Déploiement de MultiProShop sur le VPS INES

Même méthode que Digita : un projet compose séparé dans `/opt/multiproshop`, branché sur le
réseau Docker d'INES, servi par `ines-nginx`. Aucun port publié, aucun nouveau serveur SQL ou Redis.

| Élément | Où | Mémoire |
| --- | --- | --- |
| Site (gunicorn, 2 × 4 threads) | conteneur `multiproshop-web` | ≈ 160 Mo (limite 384 Mo) |
| Synchronisations CJ + planificateur (Celery `-B`) | conteneur `multiproshop-worker` | ≈ 180 Mo (limite 384 Mo) |
| Base | base `multiproshop` dans `ines-postgres` | — |
| Cache / file Celery | `ines-redis`, bases 10 et 11 | — |
| HTTPS | bloc `nginx-multiproshop.conf` dans `ines-nginx` | — |

## Avant la première mise en ligne

1. **Changer toutes les clés** qui étaient dans le `.env` versionné (elles restent lisibles dans
   l'historique git) : `SECRET_KEY`, mot de passe d'application Gmail, mot de passe et clé CJ,
   secret de webhook CJ, clés Stripe de test.
2. Copier la base SQLite vers PostgreSQL (procédure ci-dessous, étape 3).
3. Brancher le paiement sur le Stripe d'INES (étape 3 du plan).

## Procédure (sur le VPS, `ssh ines-vps`)

```bash
# 1. Code
sudo mkdir -p /opt/multiproshop && sudo chown $USER /opt/multiproshop
git clone git@github.com:INES-organisation/multiproshop.git /opt/multiproshop
cd /opt/multiproshop
cp deploy/.env.example deploy/.env && chmod 600 deploy/.env   # remplir les valeurs

# 2. Base « multiproshop » dans ines-postgres (utilisateur dédié, propriétaire de sa base)
docker exec -i ines-postgres psql -U ines -d ines_db -c "CREATE ROLE multiproshop LOGIN PASSWORD '…'"
docker exec -i ines-postgres psql -U ines -d ines_db -c "CREATE DATABASE multiproshop OWNER multiproshop"

# 3. Données : copie de instance/multiproshop.db (envoyée depuis le Mac, ex. scp vers ~/multiproshop.db)
#    vers PostgreSQL, avec vérification ligne à ligne. Le script refuse une base cible non vide.
docker network ls | grep ines            # vérifier le nom du réseau (INES_NETWORK)
docker compose -f deploy/docker-compose.yml --env-file deploy/.env build
docker compose -f deploy/docker-compose.yml --env-file deploy/.env run --rm --no-deps \
  -v ~/multiproshop.db:/data/multiproshop.db:ro multiproshop-web \
  python scripts/migrate_sqlite_to_postgres.py /data/multiproshop.db
#    → doit finir par « Copie vérifiée : toutes les tables sont identiques. »

# 4. Conteneurs
docker compose -f deploy/docker-compose.yml --env-file deploy/.env up -d
docker exec multiproshop-web python -c "import urllib.request;print(urllib.request.urlopen('http://127.0.0.1:8000/health').read())"

# 5. HTTPS (une fois le DNS de multiproshop.com propagé vers le VPS), puis nginx
bash /opt/ines/scripts/add-custom-domain.sh multiproshop.com
#    ajouter deploy/nginx-multiproshop.conf dans monitoring/nginx/nginx.conf (dépôt INES), puis :
docker exec ines-nginx nginx -t && docker exec ines-nginx nginx -s reload
```

Mise à jour : `cd /opt/multiproshop && git pull && docker compose -f deploy/docker-compose.yml --env-file deploy/.env up -d --build`

Retour arrière : retirer le bloc nginx et recharger nginx, puis
`docker compose -f deploy/docker-compose.yml down` (la base et les images envoyées sont conservées).
