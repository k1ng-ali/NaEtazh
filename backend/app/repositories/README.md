# Репозитории

Только запросы к БД, без бизнес-логики и HTTP-ошибок. Делают `flush`, но не `commit`.

| Файл | Методы |
|---|---|
| `catalog_repo.py` | `get_active_categories`, `get_published_products`, `get_published_product_by_slug` |
| `user_repo.py` | `get_by_id`, `get_by_login`, `create`, `get_all`, `get_names`, `get_active_couriers` |
| `admin_catalog_repo.py` | категории: `get_categories_with_counts`, `get_category`, `category_slug_exists`, `count_category_products`, `create_category`, `delete_category`; товары: `get_products`, `get_product`, `product_field_exists`, `create_product`, `get_product_offers`; склад: `get_warehouses`, `get_warehouse`, `get_product_stock`, `get_stock_item_for_update`, `create_stock_item` |
| `supplier_repo.py` | `get_suppliers_with_counts`, `get_supplier`, `get_supplier_for_update`, `get_active_supplier_ids`, `get_supplier_offers`, `get_offers`, `get_offer`, `get_product` |
| `pricing_repo.py` | `get_rules`, `get_rule`, `get_rule_by_category_for_update`, `create_rule`, `delete_rule`, `get_auto_priced_products`, `get_best_offers` |
| `location_repo.py` | `get_building_by_code`, `get_buildings_with_complexes`, `get_complexes`, `get_complex`, `get_buildings`, `get_building`, `complex_slug_exists`, `building_code_exists`, `create_complex`, `create_building`, `get_tariffs`, `get_tariff`, `get_effective_tariff`, `get_tariff_by_complex_for_update`, `create_tariff`, `delete_tariff` |
| `order_repo.py` | `get_products`, `get_stock_available`, `get_stock_items_for_update`, `add`, `get_order_by_token`, `get_order`, `get_order_for_update`, `get_lines`, `get_services`, `get_service`, `get_allocations`, `get_warehouse_allocations_for_update`, `get_orders`, `get_events`, `get_courier_orders` |
| `dashboard_repo.py` | `get_order_counts`, `count_waiting`, `get_delivered_money`, `get_orders_by_day`, `get_revenue_by_day`, `get_buildings`, `get_couriers_cash` |
