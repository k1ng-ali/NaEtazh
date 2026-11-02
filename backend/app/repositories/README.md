# Репозитории

Только запросы к БД, без бизнес-логики и HTTP-ошибок. Делают `flush`, но не `commit`.

| Файл | Методы |
|---|---|
| `catalog_repo.py` | `get_active_categories`, `get_published_products`, `get_published_product_by_slug` |
| `user_repo.py` | `get_by_id`, `get_by_login`, `create` |
| `admin_catalog_repo.py` | категории: `get_categories_with_counts`, `get_category`, `category_slug_exists`, `count_category_products`, `create_category`, `delete_category`; товары: `get_products`, `get_product`, `product_field_exists`, `create_product`, `get_product_offers`; склад: `get_warehouses`, `get_warehouse`, `get_product_stock`, `get_stock_item_for_update`, `create_stock_item` |
| `supplier_repo.py` | `get_suppliers_with_counts`, `get_supplier`, `get_supplier_for_update`, `get_active_supplier_ids`, `get_supplier_offers`, `get_offers`, `get_offer`, `get_product` |
| `pricing_repo.py` | `get_rules`, `get_rule`, `get_rule_by_category_for_update`, `create_rule`, `delete_rule`, `get_auto_priced_products`, `get_best_offers` |
