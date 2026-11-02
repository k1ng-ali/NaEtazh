from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.yml_feed import FeedError, FeedOffer
from app.services.supplier_service import SupplierService


def make_feed_offer(external_id: str, price: str = "100", quantity: str = "5") -> FeedOffer:
    return FeedOffer(
        external_id=external_id, name=f"Товар {external_id}", price=Decimal(price), quantity=Decimal(quantity)
    )


def make_offer(external_id: str, price: str = "100", quantity: str = "5", is_active: bool = True):
    return SimpleNamespace(
        external_id=external_id,
        price=Decimal(price),
        quantity=Decimal(quantity),
        is_active=is_active,
    )


def test_check_feed_size_rejects_empty_feed():
    with pytest.raises(FeedError):
        SupplierService._check_feed_size(feed=[], active_before=0)


def test_check_feed_size_rejects_sudden_drop():
    feed = [make_feed_offer(str(i)) for i in range(40)]

    with pytest.raises(FeedError):
        SupplierService._check_feed_size(feed=feed, active_before=3600)


def test_check_feed_size_allows_small_first_import():
    SupplierService._check_feed_size(feed=[make_feed_offer("1")], active_before=0)


def test_apply_feed_creates_updates_and_hides():
    db = AsyncMock()
    db.add_all = MagicMock()
    service = SupplierService(db=db)
    unchanged = make_offer("1")
    repriced = make_offer("2", price="100")
    gone = make_offer("3")
    returned = make_offer("4", is_active=False)

    summary = service._apply_feed(
        supplier_id=1,
        feed=[
            make_feed_offer("1"),
            make_feed_offer("2", price="120"),
            make_feed_offer("4"),
            make_feed_offer("5"),
        ],
        existing=[unchanged, repriced, gone, returned],
    )

    assert summary == {"total": 4, "created": 1, "updated": 2, "hidden": 1}
    assert repriced.price == Decimal("120")
    assert gone.is_active is False
    assert returned.is_active is True
    created = db.add_all.call_args.args[0]
    assert [offer.external_id for offer in created] == ["5"]


async def test_sync_supplier_keeps_data_when_feed_is_broken(monkeypatch):
    db = AsyncMock()
    service = SupplierService(db=db)
    supplier = SimpleNamespace(id=1, feed_url="https://example.test/yml", last_sync_error=None)
    service.repo.get_supplier = AsyncMock(return_value=supplier)
    service.repo.get_supplier_offers = AsyncMock(return_value=[])
    service._sync_out = AsyncMock(return_value="result")
    monkeypatch.setattr("app.services.supplier_service.download_feed", AsyncMock(return_value=b"<html>"))
    service._apply_feed = MagicMock()

    result = await service.sync_supplier(supplier_id=1)

    assert result == "result"
    assert supplier.last_sync_error == "Выгрузка не является корректным XML"
    service._apply_feed.assert_not_called()
    service._sync_out.assert_awaited_once_with(supplier_id=1, ok=False, error=supplier.last_sync_error)
