from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.phone import clean_display_phone, normalize_phone
from app.enums.service_request import ServiceRequestStatusEnum

# ─── Услуги ───────────────────────────────────────────────────────────────────


class ShopServiceOut(BaseModel):
    slug: str
    name: str
    summary: str | None = None
    description: str | None = None
    price_text: str | None = None
    # Для покупателя: телефон услуги или общий телефон магазина
    phone: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ShopServiceAdminOut(ShopServiceOut):
    # Для владельца phone — только свой телефон услуги, без общего
    id: int
    position: int
    is_active: bool


class ShopServiceIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    summary: str | None = Field(None, max_length=120)
    description: str | None = Field(None, max_length=2000)
    price_text: str | None = Field(None, max_length=60)
    phone: str | None = Field(None, max_length=30)
    position: int = Field(0, ge=0, le=1000)
    is_active: bool = True

    @field_validator("name", "summary", "description", "price_text")
    @classmethod
    def strip(cls, value: str | None) -> str | None:
        value = value.strip() if value else None
        return value or None

    @field_validator("phone")
    @classmethod
    def check_phone(cls, value: str | None) -> str | None:
        return clean_display_phone(value)


class ShopContactsOut(BaseModel):
    phone: str | None = None


class ShopContactsIn(BaseModel):
    phone: str | None = Field(None, max_length=30)

    @field_validator("phone")
    @classmethod
    def check_phone(cls, value: str | None) -> str | None:
        return clean_display_phone(value)


# ─── Заявки ───────────────────────────────────────────────────────────────────


class ServiceRequestCreateIn(BaseModel):
    service_slug: str = Field(min_length=1, max_length=80)
    customer_name: str = Field(min_length=1, max_length=80)
    customer_phone: str = Field(min_length=10, max_length=20)
    # Корпус из QR, иначе адрес текстом
    building_code: str | None = Field(None, max_length=32)
    address_text: str | None = Field(None, max_length=250)
    apartment: str | None = Field(None, max_length=10)
    preferred_date: date | None = None
    comment: str | None = Field(None, max_length=1000)
    source_code: str | None = Field(None, max_length=32)
    # Согласие на обработку персональных данных обязательно
    consent: Literal[True]

    @field_validator("customer_phone")
    @classmethod
    def check_phone(cls, value: str) -> str:
        return normalize_phone(value)


class ServiceRequestCreatedOut(BaseModel):
    number: int


class ServiceRequestOut(BaseModel):
    id: int
    service_name: str
    status: ServiceRequestStatusEnum
    customer_name: str
    customer_phone: str
    address: str
    preferred_date: date | None = None
    comment: str | None = None
    created_at: datetime


class ServiceRequestListOut(BaseModel):
    items: list[ServiceRequestOut]
    total: int


class ServiceRequestStatusIn(BaseModel):
    status: ServiceRequestStatusEnum
