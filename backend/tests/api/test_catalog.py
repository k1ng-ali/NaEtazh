from unittest.mock import AsyncMock

from httpx import ASGITransport, AsyncClient

from app.deps.services import get_catalog_service
from app.main import app
from app.schemas.catalog import CategoryOut


async def test_list_categories_ok():
    service = AsyncMock()
    service.list_categories.return_value = [
        CategoryOut(id=1, parent_id=None, name="Штукатурка", slug="shtukaturka", position=0)
    ]
    app.dependency_overrides[get_catalog_service] = lambda: service

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/categories/")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()[0]["slug"] == "shtukaturka"


async def test_list_products_rejects_large_limit():
    service = AsyncMock()
    app.dependency_overrides[get_catalog_service] = lambda: service

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/products/", params={"limit": 101})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    service.list_products.assert_not_called()
