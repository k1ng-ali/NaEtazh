#!/bin/sh
# Обновление на сервере: копия базы, новые образы из Docker Hub, перезапуск.
# Миграции применяются сами при старте backend.
set -eu

cd "$(dirname "$0")"
COMPOSE="docker compose -f docker-compose.prod.yml"

# Перед обновлением сохраняем базу, если сайт уже работает
if [ -n "$($COMPOSE ps --status running -q db 2>/dev/null)" ]; then
  # Упавший backend не должен мешать выкатить исправление
  sh backup.sh || echo "Копия не сделана, обновляю без неё"
fi

$COMPOSE pull
$COMPOSE up -d --remove-orphans
docker image prune -f
