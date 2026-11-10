#!/bin/sh
# Первый запуск на чистом сервере (Ubuntu 22.04 или 24.04, под root).
# Ставит Docker, создаёт deploy/.env, запускает сайт и добавляет расписание.
#
# Запуск: sh setup.sh <логин Docker Hub> <адрес сайта>
# Пример: sh setup.sh myhub http://203.0.113.10
set -eu

cd "$(dirname "$0")"
DIR=$(pwd)

HUB="${1:-}"
SITE="${2:-}"
if [ -z "$HUB" ] || [ -z "$SITE" ]; then
  echo "Использование: sh setup.sh <логин Docker Hub> <адрес сайта, например http://203.0.113.10>"
  exit 1
fi
SITE="${SITE%/}"

# ─── Docker ────────────────────────────────────────────────────────────────────
if ! command -v docker >/dev/null 2>&1; then
  echo "Ставлю Docker"
  curl -fsSL https://get.docker.com | sh
fi

# ─── Настройки ─────────────────────────────────────────────────────────────────
# Создаются один раз: повторный запуск не меняет пароли
if [ -f .env ]; then
  echo "deploy/.env уже есть, оставляю как есть"
else
  DB_PASSWORD=$(openssl rand -hex 16)
  SECRET_KEY=$(openssl rand -hex 32)
  sed \
    -e "s|your-dockerhub-login|$HUB|" \
    -e "s|__DB_PASSWORD__|$DB_PASSWORD|g" \
    -e "s|__SECRET_KEY__|$SECRET_KEY|" \
    -e "s|__SITE_URL__|$SITE|g" \
    .env.example > .env
  chmod 600 .env
  echo "Создан deploy/.env"
fi

mkdir -p logs backups
sh update.sh

# ─── Расписание ────────────────────────────────────────────────────────────────
# Выгрузка партнёра раз в час, резервная копия каждую ночь. Старые строки проекта заменяются
# Метка своя у каждого скрипта: строки продления сертификата из ssl.sh не трогаем
CRON_MARK="# stroybaza97-app"
{
  crontab -l 2>/dev/null | grep -v "$CRON_MARK" || true
  echo "0 * * * * cd $DIR && docker compose -f docker-compose.prod.yml exec -T backend python -m scripts.sync_suppliers >> $DIR/logs/sync.log 2>&1 $CRON_MARK"
  echo "30 3 * * * cd $DIR && sh backup.sh >> $DIR/logs/backup.log 2>&1 $CRON_MARK"
} | crontab -

echo
echo "Готово, сайт: $SITE"
echo "Создайте владельца (пароль спросит в терминале):"
echo "  cd $DIR && docker compose -f docker-compose.prod.yml exec backend python -m scripts.create_user --login owner --name \"Имя\" --role admin"
echo "Демо-каталог для показа: sh demo.sh"
echo "HTTPS, когда домен указывает на сервер: sh ssl.sh <почта>"
