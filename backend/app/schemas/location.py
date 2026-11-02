from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

# ─── Витрина ──────────────────────────────────────────────────────────────────


class BuildingPublicOut(BaseModel):
    """Корпус из QR-кода: подставляется в адрес доставки."""

    code: str
    name: str
    floors: int | None = None
    cargo_lift_length_mm: int | None = None
    complex_name: str
    complex_address: str | None = None


# ─── Админка ──────────────────────────────────────────────────────────────────


class ComplexIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    slug: str | None = Field(None, max_length=80, pattern=r"^[a-z0-9-]*$")
    address: str | None = Field(None, max_length=250)
    is_active: bool = True


class ComplexUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=120)
    address: str | None = Field(None, max_length=250)
    is_active: bool | None = None


class BuildingIn(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    # Пусто: сгенерируем короткий код для QR
    code: str | None = Field(None, max_length=32, pattern=r"^[a-z0-9-]*$")
    floors: int | None = Field(None, ge=1, le=100)
    cargo_lift_length_mm: int | None = Field(None, ge=0, le=10000)


class BuildingUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=60)
    floors: int | None = Field(None, ge=1, le=100)
    cargo_lift_length_mm: int | None = Field(None, ge=0, le=10000)


class BuildingOut(BaseModel):
    id: int
    complex_id: int
    name: str
    code: str
    floors: int | None = None
    cargo_lift_length_mm: int | None = None

    model_config = ConfigDict(from_attributes=True)


class ComplexOutAdmin(BaseModel):
    id: int
    name: str
    slug: str
    address: str | None = None
    is_active: bool
    buildings: list[BuildingOut] = []

    model_config = ConfigDict(from_attributes=True)


class TariffIn(BaseModel):
    # Пусто: тариф по умолчанию
    complex_id: int | None = None
    delivery_price: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    delivery_free_from: Decimal | None = Field(None, ge=0, max_digits=12, decimal_places=2)
    delivery_cost: Decimal = Field(Decimal("0"), ge=0, max_digits=12, decimal_places=2)
    lift_price_per_100kg: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    lift_min_price: Decimal = Field(Decimal("0"), ge=0, max_digits=12, decimal_places=2)
    stairs_price_per_100kg_floor: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    lifting_cost_percent: Decimal = Field(Decimal("0"), ge=0, le=100, max_digits=5, decimal_places=2)


class TariffOut(TariffIn):
    id: int
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
