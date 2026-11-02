from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.security import create_access_token, create_refresh_token
from app.deps.services import get_admin_catalog_service, get_admin_order_service, get_pricing_service
from app.main import app
from app.schemas.admin_order import OrderOutAdmin


async def request(method: str, url: str, token: str | None = None, **kwargs):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        return await client.request(method, url, headers=headers, **kwargs)


async def test_admin_requires_token():
    response = await request("GET", "/api/v1/manager/products/")

    assert response.status_code == 401


async def test_admin_rejects_refresh_token_as_access():
    response = await request("GET", "/api/v1/manager/products/", token=create_refresh_token(user_id=1))

    assert response.status_code == 401


async def test_manager_can_list_products():
    service = AsyncMock()
    service.list_products.return_value = {"items": [], "total": 0}
    app.dependency_overrides[get_admin_catalog_service] = lambda: service

    try:
        response = await request(
            "GET", "/api/v1/manager/products/", token=create_access_token(user_id=2, role="manager")
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


@pytest.mark.parametrize(
    ("role", "url"),
    [
        ("courier", "/api/v1/manager/orders/"),
        ("courier", "/api/v1/admin/dashboard/"),
        ("manager", "/api/v1/admin/dashboard/"),
        ("manager", "/api/v1/admin/users/"),
        ("manager", "/api/v1/admin/orders/1"),
        ("manager", "/api/v1/courier/orders/"),
        ("admin", "/api/v1/courier/orders/"),
    ],
)
async def test_roles_are_separated(role, url):
    response = await request("GET", url, token=create_access_token(user_id=2, role=role))

    assert response.status_code == 403


async def test_manager_order_has_no_money():
    full = {
        "id": 1,
        "public_token": "t",
        "status": "new",
        "next_statuses": [],
        "created_at": "2026-11-02T10:00:00Z",
        "updated_at": "2026-11-02T10:00:00Z",
        "customer_name": "Иван",
        "customer_phone": "+79123456789",
        "address": "ЖК",
        "lifting_type": "none",
        "lines": [],
        "services": [{"id": 1, "type": "delivery", "name": "Доставка", "price": "700", "cost": "500"}],
        "goods_total": "0",
        "services_total": "700",
        "total": "700",
        "events": [],
        "goods_cost": "0",
        "services_cost": "500",
        "profit": "200",
        "profit_complete": True,
    }
    service = AsyncMock()
    service.get_order.return_value = OrderOutAdmin(**full)
    app.dependency_overrides[get_admin_order_service] = lambda: service

    try:
        response = await request(
            "GET", "/api/v1/manager/orders/1", token=create_access_token(user_id=2, role="manager")
        )
    finally:
        app.dependency_overrides.clear()

    body = response.json()
    assert response.status_code == 200
    assert "profit" not in body and "goods_cost" not in body
    assert "cost" not in body["services"][0]
