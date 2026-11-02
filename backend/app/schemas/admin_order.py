from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.enums.order import (
    AllocationSourceEnum,
    ContactChannelEnum,
    DeliverySlotEnum,
    LiftingTypeEnum,
    MissingItemPolicyEnum,
    OrderServiceTypeEnum,
    OrderStatusEnum,
)


class OrderRowAdmin(BaseModel):
    id: int
    status: OrderStatusEnum
    created_at: datetime
    customer_name: str
    customer_phone: str
    address: str
    delivery_date: date | None = None
    delivery_slot: DeliverySlotEnum | None = None
    total: Decimal
    # Есть строки, которые берём у партнёра: нужно подтвердить наличие
    has_supplier_items: bool


class OrderListOutAdmin(BaseModel):
    items: list[OrderRowAdmin]
    total: int


class AllocationOut(BaseModel):
    source_type: AllocationSourceEnum
    # Склад или поставщик
    source_name: str
    # Ссылка на товар у партнёра, чтобы быстро проверить наличие
    source_url: str | None = None
    quantity: Decimal
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


class ServiceLineAdmin(BaseModel):
    id: int
    type: OrderServiceTypeEnum
    name: str
    price: Decimal
    cost: Decimal | None = None


class OrderOutAdmin(BaseModel):
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
    delivery_date: date | None = None
    delivery_slot: DeliverySlotEnum | None = None
    comment: str | None = None
    source_code: str | None = None
    lines: list[OrderLineAdmin]
    services: list[ServiceLineAdmin]
    goods_total: Decimal
    services_total: Decimal
    total: Decimal
    goods_cost: Decimal
    services_cost: Decimal
    profit: Decimal
    # false: у части товаров или услуг не указана себестоимость, прибыль занижена или завышена
    profit_complete: bool


class OrderStatusIn(BaseModel):
    status: OrderStatusEnum


class ServiceCostIn(BaseModel):
    cost: Decimal | None = Field(None, ge=0, max_digits=12, decimal_places=2)
