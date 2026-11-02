# Схемы

Pydantic-схемы запросов и ответов. `*In` — запрос, `*Out` — ответ, `*Update` — частичное изменение.

| Файл | Схемы |
|---|---|
| `catalog.py` | `CategoryOut`, `ProductOut`, `ProductListOut` |
| `auth.py` | `LoginIn`, `UserOut`, `TokenOut`, `CurrentUser` |
| `admin_catalog.py` | `CategoryIn`, `CategoryUpdate`, `CategoryOutAdmin`, `WarehouseOut`, `StockIn`, `StockOut`, `ProductIn`, `ProductUpdate`, `ProductOfferOut`, `ProductOutAdmin`, `ProductRowAdmin`, `ProductListOutAdmin` |
| `supplier.py` | `SupplierOut`, `SupplierSyncOut`, `OfferOut`, `OfferListOut`, `OfferLinkIn`, `OfferCreateProductIn`, `OfferCreateProductOut` |
| `pricing.py` | `PricingRuleIn`, `PricingRuleOut`, `PricingRuleSaveOut` |
