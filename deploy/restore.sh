#!/bin/sh
# Восстановление из резервной копии. Текущие база и фото заменяются.
# Так же переносятся данные с компьютера разработчика, см. deploy/README.md.
#
# Запуск: sh restore.sh backups/db-<дата>.dump [backups/media-<дата>.tar.gz]
set -eu

cd "$(dirname "$0")"
COMPOSE="docker compose -f docker-compose.prod.yml"
DB_FILE="${1:-}"
MEDIA_FILE="${2:-}"

if [ ! -f "$DB_FILE" ]; then
  echo "Использование: sh restore.sh <db.dump> [media.tar.gz]"
  exit 1
fi
if [ -n "$MEDIA_FILE" ] && ! tar -tzf "$MEDIA_FILE" media/ >/dev/null 2>&1; then
  echo "$MEDIA_FILE не архив фото: нет папки media, текущие фото не трогаю"
  exit 1
fi

# Сайт останавливаем, чтобы никто не писал в базу во время восстановления
$COMPOSE stop frontend backend
$COMPOSE exec -T db sh -c 'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists --no-owner' \
  < "$DB_FILE"
if [ -n "$MEDIA_FILE" ]; then
  $COMPOSE run --rm -T --no-deps backend sh -c 'rm -rf /app/media/* && tar -xzf - -C /app' < "$MEDIA_FILE"
fi
$COMPOSE up -d

echo "Восстановлено из $DB_FILE${MEDIA_FILE:+ и $MEDIA_FILE}"
