"""
Заказ для сотрудников.

Владелец получает *Admin со всеми деньгами. Менеджер получает *Manager: те же данные без
расходов и прибыли. Сервис один, лишние поля отрезает response_model роутера менеджера.
"""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.enums.order import (
    AllocationSourceEnum,
    ContactChannelEnum,
    DeliverySlotEnum,
    LiftingTypeEnum,
    MissingItemPolicyEnum,
    OrderEventActionEnum,
    OrderServiceTypeEnum,
    OrderStatusEnum,
)

# ─── Список ───────────────────────────────────────────────────────────────────


class OrderRowAdmin(BaseModel):
    id: int
    status: OrderStatusEnum
    created_at: datetime
    customer_name: str
    customer_phone: str
    address: str
    delivery_date: date | None = None
    delivery_slot: DeliverySlotEnum | None = None
    planned_date: date | None = None
    planned_slot: DeliverySlotEnum | None = None
    courier_name: str | None = None
    total: Decimal
    # Есть строки, которые берём у партнёра: нужно подтвердить наличие
    has_supplier_items: bool


class OrderListOutAdmin(BaseModel):
    items: list[OrderRowAdmin]
    total: int


# ─── Карточка ─────────────────────────────────────────────────────────────────


class AllocationOut(BaseModel):
    source_type: AllocationSourceEnum
    # Склад или поставщик
    source_name: str
    # Ссылка на товар у партнёра, чтобы быстро проверить наличие
    source_url: str | None = None
    quantity: Decimal
    # Закупка нужна менеджеру, чтобы заказать товар у партнёра
    unit_cost: Decimal | None = None


class OrderLineAdmin(BaseModel):
    id: int
    product_id: int
    name: str
    unit: str
    quantity: Decimal
    unit_price: Decimal
    total: Decimal
    allocations: list[AllocationOut]


class ServiceLineManager(BaseModel):
    id: int
    type: OrderServiceTypeEnum
    name: str
    price: Decimal


class ServiceLineAdmin(ServiceLineManager):
    cost: Decimal | None = None


class OrderEventOut(BaseModel):
    action: OrderEventActionEnum
    status: OrderStatusEnum | None = None
    comment: str | None = None
    # Пусто: покупатель или система
    user_name: str | None = None
    created_at: datetime


class OrderOutManager(BaseModel):
    id: int
    public_token: str
    status: OrderStatusEnum
    # Куда можно перевести заказ из текущего статуса
    next_statuses: list[OrderStatusEnum]
    created_at: datetime
    updated_at: datetime
    customer_name: str
    customer_phone: str
    contact_channel: ContactChannelEnum | None = None
    missing_item_policy: MissingItemPolicyEnum | None = None
    address: str
    entrance: str | None = None
    floor: str | None = None
    apartment: str | None = None
    lifting_type: LiftingTypeEnum
    # Пожелание покупателя
    delivery_date: date | None = None
    delivery_slot: DeliverySlotEnum | None = None
    # Согласовано менеджером
    planned_date: date | None = None
    planned_slot: DeliverySlotEnum | None = None
    courier_id: int | None = None
    courier_name: str | None = None
    cash_received: Decimal | None = None
    delivered_at: datetime | None = None
    comment: str | None = None
    source_code: str | None = None
    lines: list[OrderLineAdmin]
    services: list[ServiceLineManager]
    goods_total: Decimal
    services_total: Decimal
    total: Decimal
    events: list[OrderEventOut]


class OrderOutAdmin(OrderOutManager):
    services: list[ServiceLineAdmin]
    goods_cost: Decimal
    services_cost: Decimal
    profit: Decimal
    # false: у части товаров или услуг не указана себестоимость, прибыль приблизительная
    profit_complete: bool


# ─── Действия ─────────────────────────────────────────────────────────────────


class OrderStatusIn(BaseModel):
    status: OrderStatusEnum


class OrderDeliveryIn(BaseModel):
    courier_id: int | None = None
    planned_date: date | None = None
    planned_slot: DeliverySlotEnum | None = None


class ServiceCostIn(BaseModel):
    cost: Decimal | None = Field(None, ge=0, max_digits=12, decimal_places=2)


class CourierOut(BaseModel):
    id: int
    name: str
