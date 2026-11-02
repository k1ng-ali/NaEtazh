from sqlalchemy import select

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
