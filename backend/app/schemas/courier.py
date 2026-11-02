from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.enums.order import ContactChannelEnum, DeliverySlotEnum, LiftingTypeEnum, OrderStatusEnum


class CourierOrderRow(BaseModel):
    id: int
    status: OrderStatusEnum
    planned_date: date | None = None
    planned_slot: DeliverySlotEnum | None = None
    address: str
    lifting_type: LiftingTypeEnum
    # Сколько получить с покупателя
    total: Decimal


class CourierLineOut(BaseModel):
    name: str
    unit: str
    quantity: Decimal


class CourierOrderOut(BaseModel):
    """Только то, что нужно в дороге: без закупки, прибыли и источников товара."""

    id: int
    status: OrderStatusEnum
    planned_date: date | None = None
    planned_slot: DeliverySlotEnum | None = None
    address: str
    # Для кнопки маршрута: адрес дома без подъезда и квартиры
    map_address: str
    entrance: str | None = None
    floor: str | None = None
    apartment: str | None = None
    lifting_type: LiftingTypeEnum
    customer_name: str
    customer_phone: str
    contact_channel: ContactChannelEnum | None = None
    comment: str | None = None
    lines: list[CourierLineOut]
    total: Decimal
    cash_received: Decimal | None = None
    delivered_at: datetime | None = None


class CourierDeliverIn(BaseModel):
    cash_received: Decimal = Field(ge=0, max_digits=12, decimal_places=2)


class CourierProblemIn(BaseModel):
    comment: str = Field(min_length=1, max_length=500)
