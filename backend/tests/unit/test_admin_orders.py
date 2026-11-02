from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.enums.order import OrderStatusEnum
from app.services.admin_order_service import AdminOrderService


def make_service(order_status: str, allocations=()):
    service = AdminOrderService(db=AsyncMock())
    order = SimpleNamespace(id=1, status=order_status)
    service.repo.get_order_for_update = AsyncMock(return_value=order)
    service.repo.get_warehouse_allocations_for_update = AsyncMock(return_value=list(allocations))
    service._order_out = AsyncMock(return_value="out")
    return service, order


async def test_change_status_rejects_skipping_steps():
    service, _ = make_service(OrderStatusEnum.new.value)

    with pytest.raises(HTTPException) as exc:
        await service.change_status(order_id=1, new_status=OrderStatusEnum.delivered)

    assert exc.value.status_code == 409


async def test_cancel_releases_reserve():
    stock = SimpleNamespace(quantity=Decimal("12"), reserved=Decimal("12"))
    allocation = SimpleNamespace(quantity=Decimal("10"))
    service, order = make_service(OrderStatusEnum.confirmed.value, [(allocation, stock)])

    await service.change_status(order_id=1, new_status=OrderStatusEnum.canceled)

    assert order.status == "canceled"
    assert stock.reserved == Decimal("2")
    assert stock.quantity == Decimal("12")


async def test_delivered_writes_off_stock():
    stock = SimpleNamespace(quantity=Decimal("12"), reserved=Decimal("10"))
    allocation = SimpleNamespace(quantity=Decimal("10"))
    service, _ = make_service(OrderStatusEnum.in_delivery.value, [(allocation, stock)])

    await service.change_status(order_id=1, new_status=OrderStatusEnum.delivered)

    assert stock.reserved == Decimal("0")
    assert stock.quantity == Decimal("2")
