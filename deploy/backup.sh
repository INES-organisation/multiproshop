#!/bin/bash
# Sauvegarde quotidienne de la base MultiProShop (cron du VPS, ex. 4 h 15) :
#   15 4 * * * /opt/multiproshop/deploy/backup.sh >> /home/ubuntu/multiproshop-backups/backup.log 2>&1
# - pg_dump de la base « multiproshop » dans le conteneur ines-postgres, compressé, 14 jours gardés ;
# - copie hors VPS si BACKUP_RCLONE_REMOTE est défini dans deploy/.env (ex. « b2:multiproshop-backups »,
#   remote rclone configuré une fois sur le VPS) ;
# - en cas d'échec, notification dans l'admin (cloche) pour que la panne ne passe pas inaperçue.
set -uo pipefail
DIR=${BACKUP_DIR:-/home/ubuntu/multiproshop-backups}
KEEP_DAYS=${BACKUP_KEEP_DAYS:-14}
ENV_FILE=/opt/multiproshop/deploy/.env
REMOTE=$(grep -E '^BACKUP_RCLONE_REMOTE=' "$ENV_FILE" 2>/dev/null | cut -d= -f2-)
mkdir -p "$DIR"
DEST="$DIR/multiproshop_$(date +%Y-%m-%d_%H%M).sql.gz"

fail() {
  echo "$(date '+%F %T') ECHEC : $1"
  docker exec multiproshop-web python -c "
from app import create_app
from services.notifications import notify
with create_app().app_context():
    notify('backup', 'Sauvegarde de la base en échec', '''$1''', level='danger', dedupe='backup-failed')
" >/dev/null 2>&1
  exit 1
}

docker exec ines-postgres pg_dump -U ines -d multiproshop --no-owner --no-acl | gzip > "$DEST"
[ "${PIPESTATUS[0]}" -eq 0 ] || { rm -f "$DEST"; fail "pg_dump a échoué"; }
# Un dump valide fait plus de quelques Ko et se termine proprement
[ "$(stat -c %s "$DEST")" -gt 10000 ] && zcat "$DEST" | tail -n 5 | grep -q "PostgreSQL database dump complete" \
  || { rm -f "$DEST"; fail "dump incomplet"; }
echo "$(date '+%F %T') OK $DEST ($(du -h "$DEST" | cut -f1))"

find "$DIR" -name 'multiproshop_*.sql.gz' -mtime +"$KEEP_DAYS" -delete

if [ -n "$REMOTE" ]; then
  rclone copy "$DEST" "$REMOTE" --quiet || fail "copie hors VPS vers $REMOTE impossible"
  rclone delete "$REMOTE" --min-age "${KEEP_DAYS}d" --quiet || true
  echo "$(date '+%F %T') copie hors VPS OK ($REMOTE)"
fi
