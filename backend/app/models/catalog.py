"""
Модели каталога.

- Category: дерево категорий витрины
- Product: товар витрины и цена продажи, источник товара здесь не хранится
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
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB

from app.core.database import Base
from app.enums.product_status import ProductStatusEnum


class Category(Base):
    __tablename__ = "categories"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    parent_id = Column(BigInteger, ForeignKey("categories.id", ondelete="CASCADE"), nullable=True, index=True)
    name = Column(String, nullable=False)
    slug = Column(String, nullable=False, unique=True)
    position = Column(Integer, nullable=False, default=0, server_default="0")
    is_active = Column(Boolean, nullable=False, default=True, server_default="true")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)


class Product(Base):
    __tablename__ = "products"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    category_id = Column(
        BigInteger, ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    sku = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    slug = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=True)
    # Единица продажи: мешок, лист, шт
    unit = Column(String, nullable=False, default="шт", server_default="шт")
    price = Column(Numeric(12, 2), nullable=False)
    # Вес и объём нужны для расчёта доставки, длина для проверки лифта
    weight_kg = Column(Numeric(10, 3), nullable=True)
    volume_m3 = Column(Numeric(10, 4), nullable=True)
    length_mm = Column(Integer, nullable=True)
    images = Column(JSONB, nullable=False, default=list, server_default="[]")
    # Характеристики для карточки и фильтров
    attributes = Column(JSONB, nullable=False, default=dict, server_default="{}")
    status = Column(
        String,
        nullable=False,
        default=ProductStatusEnum.draft.value,
        server_default=ProductStatusEnum.draft.value,
        index=True,
    )
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
