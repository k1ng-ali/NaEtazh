from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict


class OfferMatchFilterEnum(str, Enum):
    unmatched = "unmatched"
    matched = "matched"
    all = "all"


class SupplierOut(BaseModel):
    id: int
    code: str
    name: str
    feed_url: str | None = None
    is_active: bool
    last_synced_at: datetime | None = None
    last_sync_error: str | None = None
    last_sync_summary: dict | None = None
    offers_active: int = 0
    offers_unmatched: int = 0

    model_config = ConfigDict(from_attributes=True)


class SupplierSyncOut(BaseModel):
    ok: bool
    error: str | None = None
    supplier: SupplierOut


class OfferOut(BaseModel):
    id: int
    supplier_id: int
    product_id: int | None = None
    product_name: str | None = None
    external_id: str
    name: str
    url: str | None = None
    vendor: str | None = None
    category_name: str | None = None
    picture_url: str | None = None
    weight_kg: Decimal | None = None
    price: Decimal
    quantity: Decimal
    is_active: bool
    last_seen_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OfferListOut(BaseModel):
    items: list[OfferOut]
    total: int


class OfferLinkIn(BaseModel):
    product_id: int


class OfferCreateProductIn(BaseModel):
    category_id: int


class OfferCreateProductOut(BaseModel):
    product_id: int
    offer: OfferOut
