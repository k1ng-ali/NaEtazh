from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.enums.order import OrderStatusEnum
from app.schemas.admin_order import OrderLineIn
from app.services.admin_order_service import AdminOrderService


def make_service(order_status: str, allocations=()):
    service = AdminOrderService(db=AsyncMock())
    order = SimpleNamespace(id=1, status=order_status, courier_id=5, total=Decimal("100"))
    service.repo.get_order_for_update = AsyncMock(return_value=order)
    service.repo.get_warehouse_allocations_for_update = AsyncMock(return_value=list(allocations))
    service.repo.add = AsyncMock()
    service._order_out = AsyncMock(return_value="out")
    return service, order


async def test_change_status_rejects_skipping_steps():
    service, _ = make_service(OrderStatusEnum.new.value)

    with pytest.raises(HTTPException) as exc:
        await service.change_status(order_id=1, new_status=OrderStatusEnum.delivered, user_id=1)

    assert exc.value.status_code == 409


async def test_cancel_releases_reserve():
    stock = SimpleNamespace(quantity=Decimal("12"), reserved=Decimal("12"))
    allocation = SimpleNamespace(quantity=Decimal("10"))
    service, order = make_service(OrderStatusEnum.confirmed.value, [(allocation, stock)])

    await service.change_status(order_id=1, new_status=OrderStatusEnum.canceled, user_id=1)

    assert order.status == "canceled"
    assert stock.reserved == Decimal("2")
    assert stock.quantity == Decimal("12")


async def test_delivered_writes_off_stock():
    stock = SimpleNamespace(quantity=Decimal("12"), reserved=Decimal("10"))
    allocation = SimpleNamespace(quantity=Decimal("10"))
    service, _ = make_service(OrderStatusEnum.in_delivery.value, [(allocation, stock)])

    await service.change_status(order_id=1, new_status=OrderStatusEnum.delivered, user_id=1)

    assert stock.reserved == Decimal("0")
    assert stock.quantity == Decimal("2")


async def test_in_delivery_requires_courier():
    service, order = make_service(OrderStatusEnum.confirmed.value)
    order.courier_id = None

    with pytest.raises(HTTPException) as exc:
        await service.change_status(order_id=1, new_status=OrderStatusEnum.in_delivery, user_id=1)

    assert exc.value.detail == "Courier not assigned"


async def test_delivered_records_cash_and_event():
    service, order = make_service(OrderStatusEnum.in_delivery.value)

    await service.apply_status(
        order=order, new_status=OrderStatusEnum.delivered, user_id=5, cash_received=Decimal("90")
    )

    assert order.cash_received == Decimal("90")
    assert order.delivered_at is not None
    event = service.repo.add.await_args.args[0]
    assert (event.action, event.status, event.user_id) == ("status", "delivered", 5)


def make_line_service(order_status: str, lines=(), product_status: str = "published"):
    service = AdminOrderService(db=AsyncMock())
    order = SimpleNamespace(id=1, status=order_status, goods_total=Decimal("1000"), total=Decimal("1300"))
    product = SimpleNamespace(
        id=5, name="Ротбанд 30 кг", unit="мешок", price=Decimal("516"), status=product_status
    )
    service.repo.get_order_for_update = AsyncMock(return_value=order)
    service.repo.get_products = AsyncMock(return_value={5: product})
    service.repo.get_lines = AsyncMock(return_value=list(lines))
    service.repo.get_stock_items_for_update = AsyncMock(return_value=[])
    service.repo.merge_line = AsyncMock()
    service.repo.add = AsyncMock()
    service.pricing.get_best_offers = AsyncMock(
        return_value={5: SimpleNamespace(id=7, quantity=Decimal("100"), price=Decimal("430"))}
    )
    service._order_out = AsyncMock(return_value="out")
    return service, order


def added(service, cls_name: str):
    return [
        call.args[0] for call in service.repo.add.await_args_list if type(call.args[0]).__name__ == cls_name
    ]


async def test_add_line_allocates_and_updates_totals():
    service, order = make_line_service(OrderStatusEnum.confirmed.value)

    await service.add_line(order_id=1, data=OrderLineIn(product_id=5, quantity=Decimal("2")), user_id=3)

    (line,) = added(service, "OrderLine")
    assert line.unit_price == Decimal("516")
    assert line.total == Decimal("1032.00")
    (allocation,) = added(service, "OrderAllocation")
    assert (allocation.source_type, allocation.quantity, allocation.unit_cost) == (
        "supplier",
        Decimal("2"),
        Decimal("430"),
    )
    assert order.goods_total == Decimal("2032.00")
    assert order.total == Decimal("2332.00")
    (event,) = added(service, "OrderEvent")
    assert event.action == "line_added"
    assert event.comment == "Ротбанд 30 кг: 2 мешок × 516 ₽"
    service.repo.merge_line.assert_not_awaited()


async def test_add_line_merges_same_product_and_price():
    existing = SimpleNamespace(id=9, product_id=5, unit_price=Decimal("516.00"))
    service, _ = make_line_service(OrderStatusEnum.new.value, lines=[existing])

    await service.add_line(order_id=1, data=OrderLineIn(product_id=5, quantity=Decimal("1")), user_id=3)

    service.repo.merge_line.assert_awaited_once()
    assert service.repo.merge_line.await_args.kwargs["target"] is existing


async def test_add_line_with_agreed_price_is_separate_line():
    existing = SimpleNamespace(id=9, product_id=5, unit_price=Decimal("516"))
    service, order = make_line_service(OrderStatusEnum.new.value, lines=[existing])

    await service.add_line(
        order_id=1,
        data=OrderLineIn(product_id=5, quantity=Decimal("1"), unit_price=Decimal("490")),
        user_id=3,
    )

    service.repo.merge_line.assert_not_awaited()
    assert order.goods_total == Decimal("1490.00")


async def test_add_line_rejected_after_dispatch():
    service, _ = make_line_service(OrderStatusEnum.in_delivery.value)

    with pytest.raises(HTTPException) as exc:
        await service.add_line(order_id=1, data=OrderLineIn(product_id=5, quantity=Decimal("1")), user_id=3)

    assert exc.value.status_code == 409


async def test_add_line_rejects_archived_product():
    service, _ = make_line_service(OrderStatusEnum.new.value, product_status="archived")

    with pytest.raises(HTTPException) as exc:
        await service.add_line(order_id=1, data=OrderLineIn(product_id=5, quantity=Decimal("1")), user_id=3)

    assert exc.value.status_code == 404


async def test_add_line_without_enough_stock_is_409():
    service, order = make_line_service(OrderStatusEnum.new.value)

    with pytest.raises(HTTPException) as exc:
        await service.add_line(order_id=1, data=OrderLineIn(product_id=5, quantity=Decimal("500")), user_id=3)

    assert exc.value.status_code == 409
    assert order.total == Decimal("1300")


def test_line_image_prefers_own_photo_then_partner():
    from app.services.admin_order_service import _line_image

    own = SimpleNamespace(id=1, images=["/media/products/own.webp"])
    partner = SimpleNamespace(id=2, images=[])
    pictures = {2: "https://partner.example/2.jpg"}

    assert _line_image(own, pictures) == "/media/products/own.webp"
    assert _line_image(partner, pictures) == "https://partner.example/2.jpg"
    assert _line_image(None, pictures) is None


def test_catalog_slug_only_for_published_products():
    from app.services.admin_order_service import _catalog_slug

    assert _catalog_slug(SimpleNamespace(slug="rotband-30", status="published")) == "rotband-30"
    assert _catalog_slug(SimpleNamespace(slug="old", status="archived")) is None
    assert _catalog_slug(None) is None
