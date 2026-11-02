from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.enums.role import UserRoleEnum
from app.schemas.user import UserUpdateIn
from app.services.courier_service import CourierService
from app.services.user_service import UserService


async def test_courier_cannot_open_foreign_order():
    service = CourierService(db=AsyncMock())
    service.repo.get_order = AsyncMock(return_value=SimpleNamespace(id=1, courier_id=7))

    with pytest.raises(HTTPException) as exc:
        await service.get_order(courier_id=8, order_id=1)

    assert exc.value.status_code == 404


async def test_courier_cannot_deliver_foreign_order():
    service = CourierService(db=AsyncMock())
    service.repo.get_order_for_update = AsyncMock(return_value=SimpleNamespace(id=1, courier_id=7))
    service.workflow.apply_status = AsyncMock()

    with pytest.raises(HTTPException):
        await service.deliver(courier_id=8, order_id=1, cash_received=Decimal("100"))

    service.workflow.apply_status.assert_not_called()


async def test_admin_cannot_deactivate_self():
    service = UserService(db=AsyncMock())
    service.repo.get_by_id = AsyncMock(return_value=SimpleNamespace(id=1, role="admin", is_active=True))

    with pytest.raises(HTTPException) as exc:
        await service.update_user(user_id=1, data=UserUpdateIn(is_active=False), current_user_id=1)

    assert exc.value.status_code == 409


async def test_admin_cannot_demote_self():
    service = UserService(db=AsyncMock())
    service.repo.get_by_id = AsyncMock(return_value=SimpleNamespace(id=1, role="admin", is_active=True))

    with pytest.raises(HTTPException):
        await service.update_user(user_id=1, data=UserUpdateIn(role=UserRoleEnum.manager), current_user_id=1)
