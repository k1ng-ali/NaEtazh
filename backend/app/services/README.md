# Сервисы

Бизнес-логика, один сервис на один домен. Сервис проверяет права и статусы, выбрасывает
`HTTPException` и делает `commit`.

| Файл | Методы |
|---|---|
| `catalog_service.py` | `list_categories`, `list_products`, `get_product` |
| `auth_service.py` | `login`, `refresh`, `get_me`, `create_user` |
| `admin_catalog_service.py` | `list_categories`, `create_category`, `update_category`, `delete_category`, `list_products`, `get_product`, `create_product`, `update_product`, `add_product_image`, `list_warehouses`, `set_stock` |
| `supplier_service.py` | `list_suppliers`, `sync_supplier`, `sync_all`, `list_offers`, `link_offer`, `unlink_offer`, `create_product_from_offer` |
| `pricing_service.py` | `list_rules`, `save_rule`, `delete_rule`, `recalc_prices` (без `commit`, вызывается из других сервисов) |

Импорт выгрузки не меняет данные, если она не скачалась, не разобралась, пуста или стала
вдвое меньше прежней. Причина сохраняется в `Supplier.last_sync_error`.
