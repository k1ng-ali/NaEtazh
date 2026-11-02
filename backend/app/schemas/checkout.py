from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.core.phone import normalize_phone
from app.enums.availability import AvailabilityEnum
from app.enums.order import (
    ContactChannelEnum,
    DeliverySlotEnum,
    LiftingTypeEnum,
    MissingItemPolicyEnum,
    OrderServiceTypeEnum,
    OrderStatusEnum,
)

# ─── Расчёт корзины ───────────────────────────────────────────────────────────


class CartItemIn(BaseModel):
    product_id: int
    quantity: Decimal = Field(gt=0, le=10000, max_digits=12, decimal_places=3)


class QuoteIn(BaseModel):
    items: list[CartItemIn] = Field(min_length=1, max_length=100)
    building_code: str | None = Field(None, max_length=32)
    floor: int | None = Field(None, ge=1, le=100)
    lifting_type: LiftingTypeEnum = LiftingTypeEnum.none


class QuoteLineOut(BaseModel):
    product_id: int
    slug: str
    name: str
    unit: str
    image: str | None = None
    quantity: Decimal
    unit_price: Decimal
    total: Decimal
    availability: AvailabilityEnum
    # Сколько можно заказать, если запрошено больше
    available_quantity: Decimal
    # Длиннее грузового лифта корпуса
    too_long_for_lift: bool = False


class ServiceOut(BaseModel):
    type: OrderServiceTypeEnum
    name: str
    price: Decimal


class QuoteOut(BaseModel):
    lines: list[QuoteLineOut]
    # Товары, которые больше не продаются: корзина их уберёт
    removed_product_ids: list[int] = []
    services: list[ServiceOut]
    goods_total: Decimal
    services_total: Decimal
    total: Decimal
    total_weight_kg: Decimal
    # У части товаров нет веса: цену подъёма уточнит менеджер
    weight_unknown: bool
    # Тарифа нет: цену доставки уточнит менеджер
    services_unknown: bool
    can_order: bool


# ─── Оформление ───────────────────────────────────────────────────────────────


class OrderCreateIn(QuoteIn):
    customer_name: str = Field(min_length=1, max_length=80)
    customer_phone: str = Field(min_length=10, max_length=20)
    contact_channel: ContactChannelEnum = ContactChannelEnum.call
    missing_item_policy: MissingItemPolicyEnum = MissingItemPolicyEnum.call
    # Если корпуса из QR нет, адрес вводится текстом
    address_text: str | None = Field(None, max_length=250)
    entrance: str | None = Field(None, max_length=10)
    apartment: str | None = Field(None, max_length=10)
    delivery_date: date | None = None
    delivery_slot: DeliverySlotEnum | None = None
    comment: str | None = Field(None, max_length=1000)
    source_code: str | None = Field(None, max_length=32)
    # Согласие на обработку персональных данных обязательно
    consent: Literal[True]

    @field_validator("customer_phone")
    @classmethod
    def check_phone(cls, value: str) -> str:
        return normalize_phone(value)


class OrderCreatedOut(BaseModel):
    number: int
    public_token: str


# ─── Статус для покупателя ────────────────────────────────────────────────────


class OrderLinePublicOut(BaseModel):
    name: str
    unit: str
    quantity: Decimal
    unit_price: Decimal
    total: Decimal


class OrderPublicOut(BaseModel):
    number: int
    status: OrderStatusEnum
    created_at: datetime
    address: str
    lifting_type: LiftingTypeEnum
    delivery_date: date | None = None
    delivery_slot: DeliverySlotEnum | None = None
    lines: list[OrderLinePublicOut]
    services: list[ServiceOut]
    goods_total: Decimal
    services_total: Decimal
    total: Decimal
