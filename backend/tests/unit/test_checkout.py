from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.core.delivery import calc_delivery_price, calc_lifting_price
from app.core.phone import normalize_phone
from app.enums.order import LiftingTypeEnum
from app.services.checkout_service import CheckoutService

TARIFF = {
    "lift_price_per_100kg": Decimal("150"),
    "lift_min_price": Decimal("300"),
    "stairs_price_per_100kg_floor": Decimal("40"),
}


def test_delivery_is_free_from_threshold():
    assert calc_delivery_price(Decimal("15000"), Decimal("700"), Decimal("15000")) == Decimal("0")
    assert calc_delivery_price(Decimal("14999"), Decimal("700"), Decimal("15000")) == Decimal("700")
    assert calc_delivery_price(Decimal("99999"), Decimal("700"), None) == Decimal("700")


def test_lifting_by_lift_counts_started_hundreds():
    price = calc_lifting_price(LiftingTypeEnum.lift, Decimal("360"), floor=7, **TARIFF)

    assert price == Decimal("600")


def test_lifting_has_min_price():
    assert calc_lifting_price(LiftingTypeEnum.lift, Decimal("30"), floor=7, **TARIFF) == Decimal("300")


def test_lifting_by_stairs_depends_on_floor():
    price = calc_lifting_price(LiftingTypeEnum.stairs, Decimal("250"), floor=5, **TARIFF)

    assert price == Decimal("600")


def test_no_lifting_is_free():
    assert calc_lifting_price(LiftingTypeEnum.none, Decimal("500"), floor=9, **TARIFF) == Decimal("0")


@pytest.mark.parametrize("raw", ["8 (912) 345-67-89", "+7 912 345 67 89", "9123456789", "79123456789"])
def test_normalize_phone(raw):
    assert normalize_phone(raw) == "+79123456789"


def test_normalize_phone_rejects_short_number():
    with pytest.raises(ValueError):
        normalize_phone("345-67-89")


def make_stock(warehouse_id: int, quantity: str, reserved: str = "0"):
    return SimpleNamespace(
        warehouse_id=warehouse_id,
        quantity=Decimal(quantity),
        reserved=Decimal(reserved),
        unit_cost=Decimal("900"),
    )


async def test_allocate_takes_stock_first_then_supplier():
    service = CheckoutService(db=AsyncMock())
    stock = make_stock(1, "12", reserved="2")
    service.repo.get_stock_items_for_update = AsyncMock(return_value=[stock])
    service.repo.add = AsyncMock()
    line = SimpleNamespace(id=10, product_id=5, quantity=Decimal("20"))
    offer = SimpleNamespace(id=7, quantity=Decimal("150"), price=Decimal("1150"))

    await service._allocate(order_line=line, offer=offer)

    allocations = [call.args[0] for call in service.repo.add.await_args_list]
    assert [(a.source_type, a.quantity) for a in allocations] == [
        ("warehouse", Decimal("10")),
        ("supplier", Decimal("10")),
    ]
    assert stock.reserved == Decimal("12")


async def test_allocate_fails_without_enough_supplier_stock():
    service = CheckoutService(db=AsyncMock())
    service.repo.get_stock_items_for_update = AsyncMock(return_value=[])
    service.repo.add = AsyncMock()
    line = SimpleNamespace(id=10, product_id=5, quantity=Decimal("20"))

    with pytest.raises(HTTPException) as exc:
        await service._allocate(
            order_line=line, offer=SimpleNamespace(id=7, quantity=Decimal("3"), price=Decimal("1"))
        )

    assert exc.value.status_code == 409
