from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.enums.role import UserRoleEnum
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.user import UserAdminOut, UserCreateIn, UserUpdateIn


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = UserRepository(db=db)

    async def list_users(self) -> list[UserAdminOut]:
        return [UserAdminOut.model_validate(user) for user in await self.repo.get_all()]

    async def create_user(self, data: UserCreateIn) -> UserAdminOut:
        if await self.repo.get_by_login(login=data.login):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Login already taken")
        user = await self.repo.create(
            login=data.login,
            password_hash=hash_password(data.password),
            name=data.name.strip(),
            role=data.role.value,
        )
        await self.db.commit()
        return UserAdminOut.model_validate(user)

    async def update_user(self, user_id: int, data: UserUpdateIn, current_user_id: int) -> UserAdminOut:
        user = await self._get_user_or_404(user_id)
        # Владелец не может случайно запереть сам себя
        if user_id == current_user_id and (
            data.is_active is False or (data.role is not None and data.role != UserRoleEnum.admin)
        ):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cannot change own access")

        if data.name is not None:
            user.name = data.name.strip()
        if data.role is not None:
            user.role = data.role.value
        if data.is_active is not None:
            if user.is_active and not data.is_active:
                # После повторного включения старые сессии не оживут
                user.session_version += 1
            user.is_active = data.is_active
        await self.db.commit()
        return UserAdminOut.model_validate(user)

    async def set_password(self, user_id: int, password: str) -> None:
        user = await self._get_user_or_404(user_id)
        user.password_hash = hash_password(password)
        # Все входы с прежним паролем завершатся, когда истечёт их токен доступа
        user.session_version += 1
        await self.db.commit()

    async def _get_user_or_404(self, user_id: int) -> User:
        user = await self.repo.get_by_id(user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return user
