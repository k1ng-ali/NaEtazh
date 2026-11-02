from sqlalchemy import select

from app.enums.role import UserRoleEnum
from app.models.user import User
from app.repositories.base_repo import BaseRepository


class UserRepository(BaseRepository):

    async def get_by_id(self, user_id: int) -> User | None:
        return await self.db.get(User, user_id)

    async def get_by_login(self, login: str) -> User | None:
        result = await self.db.execute(select(User).where(User.login == login))
        return result.scalar_one_or_none()

    async def create(self, login: str, password_hash: str, name: str, role: str) -> User:
        user = User(login=login, password_hash=password_hash, name=name, role=role)
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def get_all(self) -> list[User]:
        result = await self.db.execute(select(User).order_by(User.is_active.desc(), User.role, User.name))
        return list(result.scalars().all())

    async def get_names(self, user_ids: list[int]) -> dict[int, str]:
        if not user_ids:
            return {}
        result = await self.db.execute(select(User.id, User.name).where(User.id.in_(user_ids)))
        return {user_id: name for user_id, name in result.all()}

    async def get_active_couriers(self) -> list[User]:
        result = await self.db.execute(
            select(User)
            .where(User.role == UserRoleEnum.courier.value, User.is_active == True)  # noqa: E712
            .order_by(User.name)
        )
        return list(result.scalars().all())
