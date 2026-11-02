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
| `GET /api/v1/products/{slug}` | Один опубликованный товар с наличием |
| `GET /api/v1/buildings/{code}` | Корпус по коду из QR |
| `POST /api/v1/cart/quote` | Расчёт корзины: цены, наличие, доставка и подъём |
| `POST /api/v1/orders/` | Оформить заказ, уведомление менеджеру в Telegram |
| `GET /api/v1/orders/{token}` | Статус заказа по ссылке |

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
| `GET /api/v1/admin/orders/` | Заказы: `status`, `search` (номер, имя, телефон) |
| `GET /api/v1/admin/orders/{id}` | Заказ с источниками товаров, расходами и прибылью |
| `POST /api/v1/admin/orders/{id}/status` | Сменить статус: отмена снимает резерв, доставка списывает склад |
| `PUT /api/v1/admin/orders/{id}/services/{service_id}/cost` | Наш расход на доставку или подъём |
| `GET /api/v1/admin/complexes/` | Жилые комплексы с корпусами |
| `POST /api/v1/admin/complexes/` | Добавить комплекс |
| `PATCH /api/v1/admin/complexes/{id}` | Изменить комплекс |
| `POST /api/v1/admin/complexes/{id}/buildings` | Добавить корпус, код для QR создаётся сам |
| `PATCH /api/v1/admin/buildings/{id}` | Изменить корпус, код не меняется |
| `GET /api/v1/admin/tariffs/` | Тарифы доставки и подъёма |
| `PUT /api/v1/admin/tariffs/` | Создать или изменить тариф (только `admin`) |
| `DELETE /api/v1/admin/tariffs/{id}` | Удалить тариф комплекса (только `admin`) |
