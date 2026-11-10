from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.repositories.user_repo import UserRepository
from app.schemas.auth import TokenOut, UserOut

# Сравниваем пароль даже для несуществующего логина, чтобы время ответа не выдавало логины
_DUMMY_HASH = hash_password("dummy-password")


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = UserRepository(db=db)

    async def login(self, login: str, password: str) -> tuple[TokenOut, str]:
        """Токен доступа и refresh-токен для cookie."""
        user = await self.repo.get_by_login(login=login.strip().lower())
        password_ok = verify_password(password, user.password_hash if user else _DUMMY_HASH)
        if user is None or not password_ok or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid login or password")

        user.last_login_at = datetime.now(timezone.utc)
        await self.db.commit()
        return self._token_out(user), create_refresh_token(
            user_id=user.id, session_version=user.session_version
        )

    async def refresh(self, refresh_token: str | None) -> tuple[TokenOut, str]:
        payload = decode_token(refresh_token, "refresh") if refresh_token else None
        user = await self.repo.get_by_id(user_id=int(payload["sub"])) if payload else None
        # Токен, выданный до смены пароля или отключения, больше не продлевается
        if user is None or not user.is_active or payload.get("ver") != user.session_version:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")
        return self._token_out(user), create_refresh_token(
            user_id=user.id, session_version=user.session_version
        )

    async def get_me(self, user_id: int) -> UserOut:
        user = await self.repo.get_by_id(user_id=user_id)
        if user is None or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")
        return UserOut.model_validate(user)

    async def create_user(self, login: str, password: str, name: str, role: str) -> UserOut:
        login = login.strip().lower()
        if await self.repo.get_by_login(login=login):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Login already taken")
        user = await self.repo.create(
            login=login, password_hash=hash_password(password), name=name, role=role
        )
        await self.db.commit()
        return UserOut.model_validate(user)

    @staticmethod
    def _token_out(user) -> TokenOut:
        return TokenOut(
            access_token=create_access_token(user_id=user.id, role=user.role),
            user=UserOut.model_validate(user),
        )
