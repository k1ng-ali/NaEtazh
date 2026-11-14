from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.enums.product_status import ProductStatusEnum

# ─── Категории ────────────────────────────────────────────────────────────────


class CategoryIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    # Пусто: сделаем из названия
    slug: str | None = Field(None, max_length=80, pattern=r"^[a-z0-9-]*$")
    parent_id: int | None = None
    position: int = 0
    is_active: bool = True


class CategoryUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=120)
    slug: str | None = Field(None, min_length=1, max_length=80, pattern=r"^[a-z0-9-]+$")
    parent_id: int | None = None
    position: int | None = None
    is_active: bool | None = None


class CategoryOutAdmin(BaseModel):
    id: int
    parent_id: int | None = None
    name: str
    slug: str
    position: int
    is_active: bool
    image: str | None = None
    product_count: int = 0

    model_config = ConfigDict(from_attributes=True)


# ─── Склад ────────────────────────────────────────────────────────────────────


class WarehouseOut(BaseModel):
    id: int
    name: str
    address: str | None = None

    model_config = ConfigDict(from_attributes=True)


class StockIn(BaseModel):
    warehouse_id: int
    quantity: Decimal = Field(ge=0, max_digits=12, decimal_places=3)
    unit_cost: Decimal | None = Field(None, ge=0, max_digits=12, decimal_places=2)


class StockOut(BaseModel):
    warehouse_id: int
    warehouse_name: str
    quantity: Decimal
    reserved: Decimal
    unit_cost: Decimal | None = None


# ─── Товары ───────────────────────────────────────────────────────────────────


class ProductIn(BaseModel):
    category_id: int
    name: str = Field(min_length=1, max_length=250)
    # Пусто: сгенерируем
    sku: str | None = Field(None, max_length=64)
    slug: str | None = Field(None, max_length=80, pattern=r"^[a-z0-9-]*$")
    description: str | None = Field(None, max_length=10000)
    unit: str = Field("шт", min_length=1, max_length=20)
    price: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    is_price_manual: bool = True
    weight_kg: Decimal | None = Field(None, ge=0, max_digits=10, decimal_places=3)
    volume_m3: Decimal | None = Field(None, ge=0, max_digits=10, decimal_places=4)
    length_mm: int | None = Field(None, ge=0)
    attributes: dict[str, str] = {}
    status: ProductStatusEnum = ProductStatusEnum.draft


class ProductUpdate(BaseModel):
    category_id: int | None = None
    name: str | None = Field(None, min_length=1, max_length=250)
    sku: str | None = Field(None, min_length=1, max_length=64)
    slug: str | None = Field(None, min_length=1, max_length=80, pattern=r"^[a-z0-9-]+$")
    description: str | None = Field(None, max_length=10000)
    unit: str | None = Field(None, min_length=1, max_length=20)
    price: Decimal | None = Field(None, ge=0, max_digits=12, decimal_places=2)
    is_price_manual: bool | None = None
    weight_kg: Decimal | None = Field(None, ge=0, max_digits=10, decimal_places=3)
    volume_m3: Decimal | None = Field(None, ge=0, max_digits=10, decimal_places=4)
    length_mm: int | None = Field(None, ge=0)
    attributes: dict[str, str] | None = None
    # Только порядок и удаление уже загруженных фото
    images: list[str] | None = None
    status: ProductStatusEnum | None = None


class ProductOfferOut(BaseModel):
    id: int
    supplier_name: str
    name: str
    url: str | None = None
    price: Decimal
    quantity: Decimal
    is_active: bool


class ProductOutAdmin(BaseModel):
    id: int
    category_id: int
    sku: str
    name: str
    slug: str
    description: str | None = None
    unit: str
    price: Decimal
    is_price_manual: bool
    weight_kg: Decimal | None = None
    volume_m3: Decimal | None = None
    length_mm: int | None = None
    images: list[str]
    attributes: dict
    status: ProductStatusEnum
    created_at: datetime
    updated_at: datetime
    stock: list[StockOut] = []
    offers: list[ProductOfferOut] = []

    model_config = ConfigDict(from_attributes=True)


class ProductRowAdmin(BaseModel):
    """Строка списка товаров в админке."""

    id: int
    category_id: int
    sku: str
    name: str
    unit: str
    price: Decimal
    is_price_manual: bool
    status: ProductStatusEnum
    image: str | None = None
    stock_quantity: Decimal
    # Лучшее активное предложение партнёра
    offer_price: Decimal | None = None
    offer_quantity: Decimal | None = None


class ProductListOutAdmin(BaseModel):
    items: list[ProductRowAdmin]
    total: int
