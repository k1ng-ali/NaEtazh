"""
Модели адресов доставки.

- ResidentialComplex: жилой комплекс
- Building: корпус, code используется в ссылке QR-кода
- ServiceTariff: цены доставки и подъёма для комплекса или по умолчанию
"""

from sqlalchemy import (
    TIMESTAMP,
    BigInteger,
    Boolean,
    Column,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)

from app.core.database import Base


class ResidentialComplex(Base):
    __tablename__ = "residential_complexes"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    slug = Column(String, nullable=False, unique=True)
    address = Column(String, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, server_default="true")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)


class Building(Base):
    __tablename__ = "buildings"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    complex_id = Column(
        BigInteger,
        ForeignKey("residential_complexes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String, nullable=False)
    code = Column(String, nullable=False, unique=True)
    floors = Column(Integer, nullable=True)
    # Что может поместиться в лифт, для предупреждения о длинных материалах
    cargo_lift_length_mm = Column(Integer, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)


class ServiceTariff(Base):
    """
    Тарифы доставки и подъёма. Без жилого комплекса — тариф по умолчанию.

    Цены задаёт клиент. Расходы нужны только для расчёта прибыли.
    """

    __tablename__ = "service_tariffs"
    __table_args__ = (UniqueConstraint("complex_id", name="uq_service_tariffs_complex"),)

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    # Пусто у тарифа по умолчанию, единственность проверяет сервис
    complex_id = Column(BigInteger, ForeignKey("residential_complexes.id", ondelete="CASCADE"), nullable=True)
    delivery_price = Column(Numeric(12, 2), nullable=False)
    # Бесплатная доставка от этой суммы товаров, пусто — всегда платная
    delivery_free_from = Column(Numeric(12, 2), nullable=True)
    # Во что клиенту обходится один рейс
    delivery_cost = Column(Numeric(12, 2), nullable=False, default=0, server_default="0")
    # Подъём на грузовом лифте за каждые начатые 100 кг
    lift_price_per_100kg = Column(Numeric(12, 2), nullable=False)
    lift_min_price = Column(Numeric(12, 2), nullable=False, default=0, server_default="0")
    # Подъём по лестнице за каждые начатые 100 кг и каждый этаж
    stairs_price_per_100kg_floor = Column(Numeric(12, 2), nullable=False)
    # Доля цены подъёма, которая уходит грузчикам
    lifting_cost_percent = Column(Numeric(5, 2), nullable=False, default=0, server_default="0")
    updated_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
