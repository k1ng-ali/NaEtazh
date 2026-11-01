# Сервисы

Бизнес-логика, один сервис на один домен. Сервис проверяет права и статусы, выбрасывает
`HTTPException` и делает `commit`.

| Файл | Методы |
|---|---|
| `catalog_service.py` | `list_categories`, `list_products`, `get_product` |
