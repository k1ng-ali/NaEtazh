"""
Услуги магазина и заявки на них.

- ShopService: услуга на витрине (вынос мусора, демонтаж), текст и цену задаёт владелец
- ServiceRequest: заявка покупателя, менеджер перезванивает и называет цену
- ShopSettings: общие контакты магазина, одна строка
"""

from sqlalchemy import TIMESTAMP, BigInteger, Boolean, Column, Date, ForeignKey, Integer, String, Text, func

from app.core.database import Base
from app.enums.service_request import ServiceRequestStatusEnum


class ShopService(Base):
    __tablename__ = "shop_services"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    slug = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    # Одна строка для карточки
    summary = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    # Цена текстом: «от 1 500 ₽», «350 ₽ за м²». Пусто — цену называет менеджер
    price_text = Column(String, nullable=True)
    # Свой телефон услуги, например бригады демонтажа. Пусто — общий телефон магазина
    phone = Column(String, nullable=True)
    position = Column(Integer, nullable=False, default=0, server_default="0")
    is_active = Column(Boolean, nullable=False, default=True, server_default="true")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class ShopSettings(Base):
    __tablename__ = "shop_settings"

    # Строка всегда одна, с id 1
    id = Column(Integer, primary_key=True)
    # Телефон для кнопки «Позвонить» на странице услуг
    phone = Column(String, nullable=True)
    updated_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class ServiceRequest(Base):
    __tablename__ = "service_requests"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    service_id = Column(BigInteger, ForeignKey("shop_services.id", ondelete="SET NULL"), nullable=True)
    # Название на момент заявки: услугу могут переименовать или скрыть
    service_name = Column(String, nullable=False)
    status = Column(
        String,
        nullable=False,
        default=ServiceRequestStatusEnum.new.value,
        server_default=ServiceRequestStatusEnum.new.value,
        index=True,
    )
    customer_name = Column(String, nullable=False)
    customer_phone = Column(String, nullable=False)
    building_id = Column(BigInteger, ForeignKey("buildings.id", ondelete="SET NULL"), nullable=True)
    address_text = Column(String, nullable=True)
    apartment = Column(String, nullable=True)
    preferred_date = Column(Date, nullable=True)
    comment = Column(Text, nullable=True)
    source_code = Column(String, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
