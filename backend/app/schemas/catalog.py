from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.enums.availability import AvailabilityEnum


class CategoryOut(BaseModel):
    id: int
    parent_id: int | None = None
    name: str
    slug: str
    position: int
    # Своя картинка раздела или фото ходового товара из него и подразделов
    image: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ProductOut(BaseModel):
    id: int
    category_id: int
    sku: str
    name: str
    slug: str
    description: str | None = None
    unit: str
    price: Decimal
    weight_kg: Decimal | None = None
    length_mm: int | None = None
    images: list[str]
    attributes: dict

    model_config = ConfigDict(from_attributes=True)


class ProductListOut(BaseModel):
    items: list[ProductOut]
    total: int


class ProductDetailOut(ProductOut):
    # Наличие одной единицы: со склада, под заказ или нет
    availability: AvailabilityEnum
