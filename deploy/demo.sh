#!/bin/sh
# Демо-каталог для показа клиенту: выгрузка партнёра и 100 ходовых товаров с фото.
# Повторный запуск добирает товары и не создаёт дублей. Демо-сотрудников не создаёт:
# владельца добавляет scripts.create_user.
#
# Фото партнёра только для демо: на боевом сайте — после его письменного разрешения.
set -eu

cd "$(dirname "$0")"
COMPOSE="docker compose -f docker-compose.prod.yml"

$COMPOSE exec -T backend python -m scripts.sync_suppliers
$COMPOSE exec -T backend python -m scripts.seed_partner_demo
