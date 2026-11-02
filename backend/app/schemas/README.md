# Схемы

Pydantic-схемы запросов и ответов. `*In` — запрос, `*Out` — ответ, `*Update` — частичное изменение.

| Файл | Схемы |
|---|---|
| `catalog.py` | `CategoryOut`, `ProductOut`, `ProductListOut`, `ProductDetailOut` (товар с наличием) |
| `auth.py` | `LoginIn`, `UserOut`, `TokenOut`, `CurrentUser` |
| `admin_catalog.py` | `CategoryIn`, `CategoryUpdate`, `CategoryOutAdmin`, `WarehouseOut`, `StockIn`, `StockOut`, `ProductIn`, `ProductUpdate`, `ProductOfferOut`, `ProductOutAdmin`, `ProductRowAdmin`, `ProductListOutAdmin` |
| `supplier.py` | `SupplierOut`, `SupplierSyncOut`, `OfferOut`, `OfferListOut`, `OfferLinkIn`, `OfferCreateProductIn`, `OfferCreateProductOut` |
| `pricing.py` | `PricingRuleIn`, `PricingRuleOut`, `PricingRuleSaveOut` |
| `location.py` | `BuildingPublicOut`, `ComplexIn`, `ComplexUpdate`, `BuildingIn`, `BuildingUpdate`, `BuildingOut`, `ComplexOutAdmin`, `TariffIn`, `TariffOut` |
| `checkout.py` | `CartItemIn`, `QuoteIn`, `QuoteLineOut`, `ServiceOut`, `QuoteOut`, `OrderCreateIn`, `OrderCreatedOut`, `OrderLinePublicOut`, `OrderPublicOut` |
| `admin_order.py` | `OrderRowAdmin`, `OrderListOutAdmin`, `AllocationOut`, `OrderLineAdmin`, `ServiceLineManager`, `ServiceLineAdmin`, `OrderEventOut`, `OrderOutManager`, `OrderOutAdmin`, `OrderStatusIn`, `OrderDeliveryIn`, `ServiceCostIn`, `CourierOut` |
| `courier.py` | `CourierOrderRow`, `CourierLineOut`, `CourierOrderOut`, `CourierDeliverIn`, `CourierProblemIn` |
| `user.py` | `UserCreateIn`, `UserUpdateIn`, `UserPasswordIn`, `UserAdminOut` |
| `dashboard.py` | `DashboardDay`, `DashboardBuilding`, `DashboardCourier`, `DashboardOut` |
