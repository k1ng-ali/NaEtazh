from unittest.mock import AsyncMock

from httpx import ASGITransport, AsyncClient

from app.core.security import create_access_token, create_refresh_token
from app.deps.services import get_admin_catalog_service, get_pricing_service
from app.main import app


async def request(method: str, url: str, token: str | None = None, **kwargs):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        return await client.request(method, url, headers=headers, **kwargs)


async def test_admin_requires_token():
    response = await request("GET", "/api/v1/admin/products/")

    assert response.status_code == 401


async def test_admin_rejects_refresh_token_as_access():
    response = await request("GET", "/api/v1/admin/products/", token=create_refresh_token(user_id=1))

    assert response.status_code == 401


async def test_manager_can_list_products():
    service = AsyncMock()
    service.list_products.return_value = {"items": [], "total": 0}
    app.dependency_overrides[get_admin_catalog_service] = lambda: service

    try:
        response = await request(
            "GET", "/api/v1/admin/products/", token=create_access_token(user_id=2, role="manager")
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0}


async def test_manager_cannot_change_markup():
    service = AsyncMock()
    app.dependency_overrides[get_pricing_service] = lambda: service

    try:
        response = await request(
            "PUT",
            "/api/v1/admin/pricing-rules/",
            token=create_access_token(user_id=2, role="manager"),
            json={"category_id": None, "markup_percent": "20", "min_profit": "0"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    service.save_rule.assert_not_called()
