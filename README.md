# StroyBaza97

Интернет-магазин стройматериалов с доставкой и подъёмом в квартиру. Запуск 20 ноября 2026.

Магазин называется «Строй База» (StroyBaza), домен `stroybaza97.ru`. Как выбирали — в
[плане](docs/plan.md#название-и-домен).

## Состояние на 2 ноября 2026

| Что | Состояние |
|---|---|
| Витрина: каталог, товар, корзина, оформление, статус по ссылке, корпус по QR | Готово |
| Админка: товары, остатки, фото, импорт партнёра, сопоставление, наценка | Готово |
| Заказ: распределение склад → партнёр, доставка и подъём, уведомление в Telegram | Готово, нет токена бота |
| Кабинеты владельца, менеджера и курьера | Готово |
| Название и домен | Выбраны: «Строй База», `stroybaza97.ru` |
| Покупка домена, GitHub, сервер | Ждём клиента |
| Наполнение каталога, юридические страницы, Метрика | Не начато |

Код лежит в ветке `feature/staff-cabinets`, она содержит все этапы. В `main` ещё не слита,
в GitHub не отправлена. Подробности и что ждём от клиента — в [плане](docs/plan.md).

- [Концепция](docs/concept.md)
- [Архитектура](docs/architecture.md)
- [План до запуска](docs/plan.md)

## Стек

Nuxt 4 + Vue 3, FastAPI, PostgreSQL 16, Docker Compose, GitHub Actions, Docker Hub.

## Запуск

```bash
cp .env.example .env
docker compose up --build
docker compose exec backend python -m scripts.seed_demo
```

- Сайт: http://localhost:3000
- Вход для сотрудников: http://localhost:3000/login. Демо-владельца, менеджера и курьера
  создаёт `scripts/seed_demo.py`, логины и пароль в начале файла
- API и документация: http://localhost:8000/docs

Перед первым запуском замените значения в `.env`.

## Кабинеты сотрудников

Вход у всех один, после него каждый попадает в свой кабинет:

| Роль | Кабинет | Что может |
|---|---|---|
| `admin` — владелец | `/admin` | Сводка, деньги заказов, наценка, дома и тарифы, сотрудники, плюс всё, что менеджер |
| `manager` — менеджер | `/manager` | Заказы, назначение курьера и даты, каталог, остатки, партнёр. Без прибыли |
| `courier` — курьер | `/courier` | Только назначенные ему доставки: выехал, доставлен с суммой, проблема |

Первого владельца на сервере создаёт скрипт, пароль спрашивается в терминале. Остальных
сотрудников владелец добавляет в разделе «Сотрудники».

```bash
docker compose exec backend python -m scripts.create_user --login owner --name "Имя" --role admin
```

## Импорт партнёра

Выгрузку партнёра можно обновить кнопкой в разделе «Партнёр» или скриптом. На сервере его
запускает cron раз в час:

```cron
0 * * * * cd /opt/stroybaza97/deploy && docker compose -f docker-compose.prod.yml exec -T backend python -m scripts.sync_suppliers
```

## Проверки без Docker

Бэкенд:

```bash
cd backend
uv venv --python 3.12
uv pip install -r requirements.txt -r requirements-dev.txt
uv run --no-sync ruff check .
uv run --no-sync pytest
```

Фронтенд:

```bash
cd frontend
npm ci
npm run typecheck
npm run build
```

## Структура

```text
backend/   FastAPI, модели, миграции, тесты
frontend/  Nuxt, страницы и фичи
deploy/    Compose для сервера, nginx, обновление
docs/      Концепция, архитектура, план
```

## Ветки и выпуск

- `main` — основная ветка.
- `release` или тег `v*` — сборка и публикация образов в Docker Hub.

В настройках GitHub нужны секреты `DOCKERHUB_USERNAME` и `DOCKERHUB_TOKEN`.
На сервере обновление выполняет `deploy/update.sh`.
