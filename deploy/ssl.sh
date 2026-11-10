#!/bin/sh
# HTTPS для stroybaza97.ru: сертификат Let's Encrypt, переключение nginx на https,
# адреса сайта в .env и продление по cron. Повторный запуск безопасен.
#
# Перед запуском A-запись домена должна указывать на этот сервер, порты 80 и 443 открыты.
# Запуск: sh ssl.sh [почта для писем Let's Encrypt о сроке сертификата]
set -eu

cd "$(dirname "$0")"
DIR=$(pwd)
COMPOSE="docker compose -f docker-compose.prod.yml"
DOMAIN=stroybaza97.ru
EMAIL="${1:-}"

if [ ! -f .env ]; then
  echo "Нет deploy/.env: сначала sh setup.sh"
  exit 1
fi

# www добавляем в сертификат, только если для него есть запись в DNS
DOMAINS="-d $DOMAIN"
if getent hosts "www.$DOMAIN" >/dev/null; then
  DOMAINS="$DOMAINS -d www.$DOMAIN"
else
  echo "Для www.$DOMAIN нет записи в DNS, сертификат только на $DOMAIN"
fi
if [ -n "$EMAIL" ]; then
  CONTACT="--email $EMAIL"
else
  CONTACT="--register-unsafely-without-email"
fi

# ─── Сертификат ────────────────────────────────────────────────────────────────
# nginx должен отвечать по http: через него Let's Encrypt проверяет домен
$COMPOSE up -d nginx
# shellcheck disable=SC2086
$COMPOSE run --rm certbot certonly --webroot -w /var/www/certbot \
  $DOMAINS $CONTACT --agree-tos --non-interactive --keep-until-expiring

# ─── Настройки ─────────────────────────────────────────────────────────────────
set_env() {
  if grep -q "^$1=" .env; then
    sed -i "s|^$1=.*|$1=$2|" .env
  else
    echo "$1=$2" >> .env
  fi
}
SITE="https://$DOMAIN"
set_env NGINX_SITE https
set_env COOKIE_SECURE true
set_env CORS_ORIGINS "$SITE"
set_env SITE_URL "$SITE"
set_env NUXT_PUBLIC_SITE_URL "$SITE"

# Контейнеры пересоздаются с новыми настройками
$COMPOSE up -d

# ─── Продление ─────────────────────────────────────────────────────────────────
# Certbot продлевает за 30 дней до конца срока, nginx перечитывает сертификат
CRON_MARK="# stroybaza97-ssl"
{
  crontab -l 2>/dev/null | grep -v "$CRON_MARK" || true
  echo "15 4 * * * cd $DIR && ($COMPOSE run --rm certbot renew -q && $COMPOSE exec -T nginx nginx -s reload) >> $DIR/logs/ssl.log 2>&1 $CRON_MARK"
} | crontab -

echo "Готово: $SITE"
