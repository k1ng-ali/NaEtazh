from pydantic import BaseModel, ConfigDict, Field

from app.enums.role import UserRoleEnum


class LoginIn(BaseModel):
    login: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class UserOut(BaseModel):
    id: int
    login: str
    name: str
    role: UserRoleEnum

    model_config = ConfigDict(from_attributes=True)


class TokenOut(BaseModel):
    access_token: str
    user: UserOut


class CurrentUser(BaseModel):
    """Пользователь из access-токена, без запроса к БД."""

    id: int
    role: UserRoleEnum
