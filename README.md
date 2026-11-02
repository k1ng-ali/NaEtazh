# StroyBaza97

Интернет-магазин стройматериалов с доставкой и подъёмом в квартиру.

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
- Админка: http://localhost:3000/admin, демо-вход создаёт `scripts/seed_demo.py` (логин и пароль в начале файла)
- API и документация: http://localhost:8000/docs

Перед первым запуском замените значения в `.env`.

## Сотрудники и импорт партнёра

Сотрудника создаёт скрипт, пароль спрашивается в терминале:

```bash
docker compose exec backend python -m scripts.create_user --login ivan --name "Иван" --role manager
```

Роли: `admin` — всё, включая наценку; `manager` — каталог, остатки, сопоставление.

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
