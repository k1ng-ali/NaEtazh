# Сервер

Как это устроено: push в ветку `release` → GitHub Actions собирает образы backend и frontend и
кладёт их в Docker Hub → на сервере `update.sh` скачивает образы и перезапускает сайт.
Миграции базы применяются сами при старте backend.

Сайт работает на `https://stroybaza97.ru`. Сертификат Let's Encrypt выпускает и продлевает
`ssl.sh`. Запросы по http, по IP и на `www` перенаправляются на `https://stroybaza97.ru`.

## Скрипты

| Скрипт | Что делает | Когда |
|---|---|---|
| `setup.sh <логин Docker Hub> <адрес>` | Ставит Docker, создаёт `.env` с паролями, запускает сайт по http, добавляет cron | Один раз на новом сервере |
| `ssl.sh [почта]` | Выпускает сертификат, включает https, ставит адреса сайта в `.env`, добавляет продление в cron | Один раз после `setup.sh`, когда домен указывает на сервер |
| `update.sh` | Копия базы, `docker compose pull`, перезапуск | После каждого релиза |
| `backup.sh` | Копия базы и фото в `backups/`, хранит 14 последних | Каждую ночь в 3:30 по cron и перед обновлением |
| `restore.sh <db.dump> [media.tar.gz]` | Заменяет базу и фото копией | При сбое или переносе данных |

Cron: выгрузка партнёра и докачка фото раз в час, копия в 3:30, продление сертификата в 4:15. Логи —
в `deploy/logs/`.

Настройки nginx лежат в `nginx/`: `http.conf` для первого запуска, `https.conf` после
`ssl.sh`, общие правила в `locations.conf` и `zones.conf`. Какой сайт включён, задаёт
`NGINX_SITE` в `.env`.

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

### 2. Домен

У регистратора домена в DNS добавить A-записи на IP сервера:

| Имя | Тип | Значение |
|---|---|---|
| `@` (`stroybaza97.ru`) | A | IP сервера |
| `www` | A | IP сервера |

Записи расходятся от нескольких минут до нескольких часов. Проверка с любого компьютера:
`nslookup stroybaza97.ru` должен показать IP сервера.

### 3. Сервер

Ubuntu 22.04 или 24.04, от 2 ГБ памяти, открыты порты 22, 80 и 443. Кода на сервере нет:
только папка `deploy`, образы приходят из Docker Hub.

Со своего компьютера, из корня проекта, скопировать папку `deploy`:

```bash
ssh deploy@<IP> mkdir -p stroybaza97
```

```bash
scp -r deploy deploy@<IP>:stroybaza97/
```

Дальше на сервере. Подойдёт root или пользователь с sudo: `setup.sh` добавит его в группу
docker и попросит перезайти по ssh, после этого его нужно запустить ещё раз.

```bash
cd ~/stroybaza97/deploy && sh setup.sh <логин Docker Hub> http://stroybaza97.ru
```

Если закрыты образы в Docker Hub, перед `setup.sh` выполнить `docker login`.

Когда `nslookup` показывает IP сервера, включить HTTPS. Почта нужна для писем Let's Encrypt,
если сертификат не продлится. Запуская скрипт, вы принимаете условия Let's Encrypt:

```bash
sh ssl.sh <почта>
```

Создать владельца, пароль спросит в терминале:

```bash
docker compose -f docker-compose.prod.yml exec backend python -m scripts.create_user --login owner --name "Имя" --role admin
```

Дальше владелец задаёт наценку в разделе «Наценка» и включает «Товары партнёра на витрине»
в разделе «Партнёр» — см. [Товары партнёра](#товары-партнёра). Потом владелец заходит на `https://stroybaza97.ru/login`, добавляет ЖК и корпуса в разделе
«Дома», менеджера и курьера в разделе «Сотрудники».

Если DNS ещё не обновился, а показать нужно сейчас, сайт уже открывается по
`http://<IP сервера>`. После `ssl.sh` такой адрес будет перенаправлять на домен.

## Товары партнёра

Тумблер «Товары партнёра на витрине» в разделе «Партнёр» сразу заводит товар витрины на каждое
предложение выгрузки. Разделы повторяют два верхних уровня дерева партнёра. Покупатель видит
товар, когда тумблер включён, товар есть в наличии у партнёра или на своём складе и есть
правило наценки. Без наценки товары партнёра не показываются: цена была бы закупочной.
Выключенный тумблер прячет товары партнёра, товары и их фото остаются.

Фото партнёр разрешил копировать. Их качает cron вместе с выгрузкой, до 1500 за запуск,
сначала товары в наличии. Чтобы не ждать, первый раз можно скачать все:

```bash
docker compose -f docker-compose.prod.yml exec -T backend python -m scripts.sync_suppliers --photos 5000
```

На сервере, где был демо-каталог, один раз перенести его 100 товаров в разделы партнёра и
убрать старые 11 разделов:

```bash
docker compose -f docker-compose.prod.yml exec -T backend python -m scripts.retire_demo_catalog
```

## Обновление

```bash
git push origin main:release
```

Дождаться «Publish images» в Actions, потом на сервере:

```bash
cd ~/stroybaza97/deploy && sh update.sh
```

Если в релизе менялись файлы самой папки `deploy` (`docker-compose.prod.yml`, `nginx/`,
скрипты), перед `update.sh` скопировать её заново той же командой `scp`. `deploy/.env`,
копии и логи на сервере при этом не затираются: в репозитории их нет.

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
scp local.dump local-media.tar.gz deploy@<IP>:stroybaza97/deploy/backups/
```

На сервере:

```bash
cd ~/stroybaza97/deploy && sh restore.sh backups/local.dump backups/local-media.tar.gz
```
