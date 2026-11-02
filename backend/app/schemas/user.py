from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.enums.role import UserRoleEnum

LOGIN_PATTERN = r"^[a-z0-9._-]{3,32}$"
MIN_PASSWORD_LENGTH = 10


class UserCreateIn(BaseModel):
    login: str = Field(pattern=LOGIN_PATTERN)
    name: str = Field(min_length=1, max_length=80)
    role: UserRoleEnum
    password: str = Field(min_length=MIN_PASSWORD_LENGTH, max_length=128)


class UserUpdateIn(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=80)
    role: UserRoleEnum | None = None
    is_active: bool | None = None


class UserPasswordIn(BaseModel):
    password: str = Field(min_length=MIN_PASSWORD_LENGTH, max_length=128)


class UserAdminOut(BaseModel):
    id: int
    login: str
    name: str
    role: UserRoleEnum
    is_active: bool
    last_login_at: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
