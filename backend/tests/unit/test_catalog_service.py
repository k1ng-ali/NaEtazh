from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.services.catalog_service import CatalogService


def make_product(**overrides):
    values = {
        "id": 1,
        "category_id": 1,
        "sku": "SKU-1",
        "name": "Ротбанд 30 кг",
        "slug": "rotband-30",
        "description": None,
        "unit": "мешок",
        "price": Decimal("430.00"),
        "weight_kg": Decimal("30.000"),
        "length_mm": None,
        "images": [],
        "attributes": {},
    }
    return SimpleNamespace(**{**values, **overrides})


async def test_get_product_not_found():
    service = CatalogService(db=AsyncMock())
    service.repo.get_published_product_by_slug = AsyncMock(return_value=None)

    with pytest.raises(HTTPException) as exc:
        await service.get_product(slug="missing")

    assert exc.value.status_code == 404


async def test_list_products_returns_items_and_total():
    service = CatalogService(db=AsyncMock())
    service.repo.get_published_products = AsyncMock(return_value=([make_product()], 7))
    service.repo.get_partner_pictures = AsyncMock(return_value={})

    result = await service.list_products(category_slug="shtukaturka", search="рот", skip=0, limit=1)

    service.repo.get_published_products.assert_awaited_once_with(
        category_slug="shtukaturka",
        search="рот",
        skip=0,
        limit=1,
    )
    assert result.total == 7
    assert result.items[0].slug == "rotband-30"
    assert result.items[0].price == Decimal("430.00")


async def test_list_products_uses_partner_photo_until_own_copy():
    service = CatalogService(db=AsyncMock())
    own = make_product(id=1, images=["/media/products/own.webp"])
    partner = make_product(id=2, slug="vetonit", images=[])
    service.repo.get_published_products = AsyncMock(return_value=([own, partner], 2))
    service.repo.get_partner_pictures = AsyncMock(return_value={2: "https://partner.example/2.jpg"})

    result = await service.list_products()

    service.repo.get_partner_pictures.assert_awaited_once_with([2])
    assert [item.images for item in result.items] == [
        ["/media/products/own.webp"],
        ["https://partner.example/2.jpg"],
    ]
