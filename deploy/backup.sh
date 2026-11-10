#!/bin/sh
# Резервная копия базы и фото в deploy/backups. Хранятся 14 последних.
set -eu

cd "$(dirname "$0")"
COMPOSE="docker compose -f docker-compose.prod.yml"
STAMP=$(date +%Y%m%d-%H%M%S)
KEEP=14

mkdir -p backups
# Недописанная копия хуже никакой: при ошибке удаляем файлы этого запуска
trap 'rm -f "backups/db-$STAMP.dump" "backups/media-$STAMP.tar.gz"; echo "Копия не сделана" >&2' EXIT
$COMPOSE exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom' \
  > "backups/db-$STAMP.dump"
$COMPOSE exec -T backend tar -czf - -C /app media > "backups/media-$STAMP.tar.gz"
trap - EXIT

# Старые копии удаляем
ls -1t backups/db-*.dump | tail -n +$((KEEP + 1)) | xargs -r rm --
ls -1t backups/media-*.tar.gz | tail -n +$((KEEP + 1)) | xargs -r rm --

echo "Копия: backups/db-$STAMP.dump, backups/media-$STAMP.tar.gz"
