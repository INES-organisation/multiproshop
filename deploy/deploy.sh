#!/bin/bash
# Déploiement de MultiProShop sur le VPS : ssh ines-vps /opt/multiproshop/deploy/deploy.sh
# 1. sauvegarde de la base (deploy/backup.sh) ; on s'arrête si elle échoue ;
# 2. journaux des conteneurs gardés dans /home/ubuntu/multiproshop-logs (30 jours) : docker les efface
#    quand il recrée un conteneur ;
# 3. code à jour depuis main, nouvelle image et redémarrage.
set -euo pipefail
cd /opt/multiproshop
LOGS=${MPS_LOG_DIR:-/home/ubuntu/multiproshop-logs}
mkdir -p "$LOGS"
./deploy/backup.sh
stamp=$(date +%Y-%m-%d_%H%M)
for c in multiproshop-web multiproshop-worker; do
  docker logs --timestamps "$c" 2>&1 | gzip > "$LOGS/${c}_$stamp.log.gz" || true
done
find "$LOGS" -name '*.log.gz' -mtime +30 -delete
git pull --ff-only origin main
docker compose -f deploy/docker-compose.yml --env-file deploy/.env up -d --build
