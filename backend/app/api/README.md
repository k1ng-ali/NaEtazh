# API

Роутеры тонкие: принимают параметры, вызывают один метод сервиса и возвращают результат.

Домены по ролям. Права проверяет сервер, а не только интерфейс:

| Домен | Кто | Префикс |
|---|---|---|
| `platform` | покупатели, без входа | `/api/v1` |
| `manager` | менеджер и владелец | `/api/v1/manager` |
| `courier` | только курьер, только свои заказы | `/api/v1/courier` |
| `admin` | только владелец | `/api/v1/admin` |

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

## Manager

| Метод и путь | Описание |
|---|---|
| `GET /manager/orders/` | Заказы: `status`, `search` (номер, имя, телефон) |
| `GET /manager/orders/{id}` | Заказ с источниками и историей, без расходов и прибыли |
| `POST /manager/orders/{id}/status` | Сменить статус: отмена снимает резерв, доставка списывает склад |
| `PUT /manager/orders/{id}/delivery` | Курьер, согласованная дата и время |
| `GET /manager/couriers/` | Активные курьеры для назначения |
| `GET /manager/categories/` | Все категории с числом товаров |
| `POST /manager/categories/` | Создать категорию |
| `PATCH /manager/categories/{id}` | Изменить категорию |
| `DELETE /manager/categories/{id}` | Удалить пустую категорию |
| `GET /manager/products/` | Товары с остатком и ценой партнёра: `search`, `category_id`, `status` |
| `POST /manager/products/` | Создать товар |
| `GET /manager/products/{id}` | Товар с остатками и предложениями партнёра |
| `PATCH /manager/products/{id}` | Изменить товар, порядок и удаление фото |
| `POST /manager/products/{id}/images` | Загрузить фото, сервер сжимает в WebP |
| `PUT /manager/products/{id}/stock` | Остаток и себестоимость на складе |
| `GET /manager/warehouses/` | Склады |
| `GET /manager/suppliers/` | Поставщики и итог последнего импорта |
| `POST /manager/suppliers/{id}/sync` | Загрузить выгрузку поставщика |
| `GET /manager/offers/` | Предложения: `match`, `search`, `in_stock` |
| `POST /manager/offers/{id}/link` | Привязать предложение к товару |
| `POST /manager/offers/{id}/unlink` | Отвязать |
| `POST /manager/offers/{id}/create-product` | Черновик товара из предложения |

## Courier

Чужой заказ для курьера отвечает 404, чтобы не подсказывать, что такой номер есть.

| Метод и путь | Описание |
|---|---|
| `GET /courier/orders/` | Свои активные доставки и отвезённые сегодня |
| `GET /courier/orders/{id}` | Адрес, телефон, состав и сумма, без закупки и прибыли |
| `POST /courier/orders/{id}/start` | Выехал |
| `POST /courier/orders/{id}/deliver` | Доставлен с суммой наличных; расхождение уходит менеджеру в Telegram |
| `POST /courier/orders/{id}/problem` | Проблема: в историю заказа и в Telegram |

## Admin

| Метод и путь | Описание |
|---|---|
| `GET /admin/dashboard/` | Сводка за `days` дней: выручка, прибыль, корпуса, наличные у курьеров |
| `GET /admin/orders/{id}` | Заказ с расходами и прибылью |
| `PUT /admin/orders/{id}/services/{service_id}/cost` | Наш расход на доставку или подъём |
| `GET /admin/users/` | Сотрудники |
| `POST /admin/users/` | Добавить сотрудника |
| `PATCH /admin/users/{id}` | Имя, роль, отключение. Себя отключить или понизить нельзя |
| `PUT /admin/users/{id}/password` | Новый пароль |
| `GET /admin/pricing-rules/` | Правила наценки |
| `PUT /admin/pricing-rules/` | Создать или изменить правило и пересчитать цены |
| `DELETE /admin/pricing-rules/{id}` | Удалить правило |
| `GET /admin/complexes/` | Жилые комплексы с корпусами |
| `POST /admin/complexes/` | Добавить комплекс |
| `PATCH /admin/complexes/{id}` | Изменить комплекс |
| `POST /admin/complexes/{id}/buildings` | Добавить корпус, код для QR создаётся сам |
| `PATCH /admin/buildings/{id}` | Изменить корпус, код не меняется |
| `GET /admin/tariffs/` | Тарифы доставки и подъёма |
| `PUT /admin/tariffs/` | Создать или изменить тариф |
| `DELETE /admin/tariffs/{id}` | Удалить тариф комплекса |
