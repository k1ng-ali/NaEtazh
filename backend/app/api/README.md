# API

Роутеры тонкие: принимают параметры, вызывают один метод сервиса и возвращают результат.

## Auth

| Метод и путь | Описание |
|---|---|
| `POST /api/v1/auth/login` | Вход сотрудника: access-токен в ответе, refresh в httpOnly cookie |
| `POST /api/v1/auth/refresh` | Новый access-токен по cookie |
| `POST /api/v1/auth/logout` | Удаляет cookie |
| `GET /api/v1/auth/me` | Текущий сотрудник |

## Platform

| Метод и путь | Описание |
|---|---|
| `GET /api/v1/categories/` | Активные категории |
| `GET /api/v1/products/` | Товары: `category`, `search`, `skip`, `limit` |
| `GET /api/v1/products/{slug}` | Один опубликованный товар |

## Admin

Все пути требуют роль `manager` или `admin`. Изменять наценку может только `admin`.

| Метод и путь | Описание |
|---|---|
| `GET /api/v1/admin/categories/` | Все категории с числом товаров |
| `POST /api/v1/admin/categories/` | Создать категорию |
| `PATCH /api/v1/admin/categories/{id}` | Изменить категорию |
| `DELETE /api/v1/admin/categories/{id}` | Удалить пустую категорию |
| `GET /api/v1/admin/products/` | Товары с остатком и ценой партнёра: `search`, `category_id`, `status` |
| `POST /api/v1/admin/products/` | Создать товар |
| `GET /api/v1/admin/products/{id}` | Товар с остатками и предложениями партнёра |
| `PATCH /api/v1/admin/products/{id}` | Изменить товар, порядок и удаление фото |
| `POST /api/v1/admin/products/{id}/images` | Загрузить фото, сервер сжимает в WebP |
| `PUT /api/v1/admin/products/{id}/stock` | Остаток и себестоимость на складе |
| `GET /api/v1/admin/warehouses/` | Склады |
| `GET /api/v1/admin/suppliers/` | Поставщики и итог последнего импорта |
| `POST /api/v1/admin/suppliers/{id}/sync` | Загрузить выгрузку поставщика |
| `GET /api/v1/admin/offers/` | Предложения: `match`, `search`, `in_stock` |
| `POST /api/v1/admin/offers/{id}/link` | Привязать предложение к товару |
| `POST /api/v1/admin/offers/{id}/unlink` | Отвязать |
| `POST /api/v1/admin/offers/{id}/create-product` | Черновик товара из предложения |
| `GET /api/v1/admin/pricing-rules/` | Правила наценки |
| `PUT /api/v1/admin/pricing-rules/` | Создать или изменить правило и пересчитать цены |
| `DELETE /api/v1/admin/pricing-rules/{id}` | Удалить правило |
