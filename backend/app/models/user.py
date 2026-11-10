"""
Сотрудники клиента. Покупатели аккаунтов не имеют.
"""

from sqlalchemy import TIMESTAMP, BigInteger, Boolean, Column, Integer, String, func

from app.core.database import Base
from app.enums.role import UserRoleEnum


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    login = Column(String, nullable=False, unique=True)
    password_hash = Column(String, nullable=False)
    name = Column(String, nullable=False)
    role = Column(
        String,
        nullable=False,
        default=UserRoleEnum.manager.value,
        server_default=UserRoleEnum.manager.value,
    )
    is_active = Column(Boolean, nullable=False, default=True, server_default="true")
    # Попадает в refresh-токен. Смена пароля и отключение увеличивают её, старые сессии перестают продлеваться
    session_version = Column(Integer, nullable=False, default=0, server_default="0")
    last_login_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
