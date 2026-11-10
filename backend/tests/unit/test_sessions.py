from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.core.security import _create_token, create_refresh_token, decode_token
from app.schemas.user import UserUpdateIn
from app.services.auth_service import AuthService
from app.services.user_service import UserService


def make_user(**kwargs):
    data = dict(
        id=5,
        login="anna",
        name="Анна",
        role="manager",
        is_active=True,
        session_version=0,
        last_login_at=None,
        created_at=datetime.now(timezone.utc),
    )
    return SimpleNamespace(**{**data, **kwargs})


def auth_service(user):
    service = AuthService(db=AsyncMock())
    service.repo.get_by_id = AsyncMock(return_value=user)
    return service


def user_service(user):
    service = UserService(db=AsyncMock())
    service.repo.get_by_id = AsyncMock(return_value=user)
    return service


async def test_refresh_keeps_session_version():
    user = make_user(session_version=3)

    _, new_token = await auth_service(user).refresh(create_refresh_token(user_id=5, session_version=3))

    assert decode_token(new_token, "refresh")["ver"] == 3


async def test_password_change_ends_old_sessions():
    user = make_user()
    old_token = create_refresh_token(user_id=5, session_version=user.session_version)

    await user_service(user).set_password(user_id=5, password="new-password-123")

    with pytest.raises(HTTPException) as exc:
        await auth_service(user).refresh(old_token)
    assert exc.value.status_code == 401


async def test_deactivation_ends_sessions_even_after_reactivation():
    user = make_user()
    old_token = create_refresh_token(user_id=5, session_version=user.session_version)
    service = user_service(user)

    await service.update_user(user_id=5, data=UserUpdateIn(is_active=False), current_user_id=1)
    await service.update_user(user_id=5, data=UserUpdateIn(is_active=True), current_user_id=1)

    assert user.is_active
    with pytest.raises(HTTPException) as exc:
        await auth_service(user).refresh(old_token)
    assert exc.value.status_code == 401


async def test_rename_keeps_sessions():
    user = make_user()
    old_token = create_refresh_token(user_id=5, session_version=user.session_version)

    await user_service(user).update_user(user_id=5, data=UserUpdateIn(name="Анна П."), current_user_id=1)

    await auth_service(user).refresh(old_token)


async def test_refresh_token_without_version_is_rejected():
    # Токены, выданные до появления версии сессий
    token = _create_token(user_id=5, token_type="refresh", expires_in=timedelta(days=1))

    with pytest.raises(HTTPException):
        await auth_service(make_user()).refresh(token)
