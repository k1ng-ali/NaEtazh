#!/bin/sh
# Обновление на сервере: скачать новые образы и перезапустить сервисы
set -eu

cd "$(dirname "$0")"

docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d --remove-orphans
docker image prune -f
