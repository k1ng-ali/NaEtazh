# Сервер

Как это устроено: push в ветку `release` → GitHub Actions собирает образы backend и frontend и
кладёт их в Docker Hub → на сервере `update.sh` скачивает образы и перезапускает сайт.
Миграции базы применяются сами при старте backend.

Пока домена нет, сайт открывается по IP сервера по http. HTTPS подключается после покупки
домена `stroybaza97.ru`.

## Скрипты

| Скрипт | Что делает | Когда |
|---|---|---|
| `setup.sh <логин Docker Hub> <адрес>` | Ставит Docker, создаёт `.env` с паролями, запускает сайт, добавляет cron | Один раз на новом сервере |
| `update.sh` | `git pull`, копия базы, новые образы, перезапуск | После каждого релиза |
| `demo.sh` | Выгрузка партнёра и 100 товаров с фото | Для показа клиенту |
| `backup.sh` | Копия базы и фото в `backups/`, хранит 14 последних | Каждую ночь в 3:30 по cron и перед обновлением |
| `restore.sh <db.dump> [media.tar.gz]` | Заменяет базу и фото копией | При сбое или переносе данных |

Cron, который ставит `setup.sh`: выгрузка партнёра раз в час и ночная копия. Логи —
в `deploy/logs/`.

## Первый запуск

### 1. GitHub

В репозитории: Settings → Secrets and variables → Actions → New repository secret.

| Секрет | Значение |
|---|---|
| `DOCKERHUB_USERNAME` | Логин Docker Hub |
| `DOCKERHUB_TOKEN` | Docker Hub → Account settings → Personal access tokens, права Read & Write |

Отправить код и собрать образы:

```bash
git push origin main
```

```bash
git push origin main:release
```

Во вкладке Actions должны пройти «CI» и «Publish images». В Docker Hub появятся
`<логин>/stroybaza97-backend` и `<логин>/stroybaza97-frontend`.

### 2. Сервер

Ubuntu 22.04 или 24.04, от 2 ГБ памяти, открыты порты 22 и 80. Всё ниже — под root.

```bash
git clone -b release https://github.com/k1ng-ali/NaEtazh.git /opt/stroybaza97
```

```bash
cd /opt/stroybaza97/deploy && sh setup.sh <логин Docker Hub> http://<IP сервера>
```

Если репозиторий закрытый, `git clone` спросит логин и токен GitHub (Settings → Developer
settings → Personal access tokens, право Contents: Read). Если закрыты образы в Docker Hub,
перед `setup.sh` выполнить `docker login`.

Создать владельца, пароль спросит в терминале:

```bash
docker compose -f docker-compose.prod.yml exec backend python -m scripts.create_user --login owner --name "Имя" --role admin
```

Для показа заполнить каталог:

```bash
sh demo.sh
```

Дальше владелец заходит на `http://<IP>/login`, добавляет ЖК и корпуса в разделе «Дома»,
менеджера и курьера в разделе «Сотрудники».

## Обновление

```bash
git push origin main:release
```

Дождаться «Publish images» в Actions, потом на сервере:

```bash
cd /opt/stroybaza97/deploy && sh update.sh
```

## Перенос данных с компьютера разработчика

Если на сервере нужен ровно тот каталог, что собран локально. Вместе с данными переедут
локальные сотрудники с демо-паролем, после переноса их пароли нужно сменить.

На своём компьютере, из корня проекта:

```bash
docker compose exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom' > local.dump
```

```bash
tar -czf local-media.tar.gz -C backend media
```

```bash
scp local.dump local-media.tar.gz root@<IP>:/opt/stroybaza97/deploy/backups/
```

На сервере:

```bash
cd /opt/stroybaza97/deploy && sh restore.sh backups/local.dump backups/local-media.tar.gz
```

## После покупки домена

1. A-запись `stroybaza97.ru` и `www` на IP сервера.
2. HTTPS через certbot и блок `listen 443` в `nginx.conf`.
3. В `deploy/.env`: адрес `https://stroybaza97.ru` в `CORS_ORIGINS`, `SITE_URL`,
   `NUXT_PUBLIC_SITE_URL`, и `COOKIE_SECURE=true`. Потом `sh update.sh`.
