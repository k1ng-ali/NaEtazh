"""
Модели источников товара.

- Warehouse и StockItem: собственный склад и остатки
- Supplier и SupplierOffer: поставщик и его предложения из выгрузки
"""

from sqlalchemy import (
    TIMESTAMP,
    BigInteger,
    Boolean,
    Column,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB

from app.core.database import Base


class Warehouse(Base):
    __tablename__ = "warehouses"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    address = Column(String, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, server_default="true")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)


class StockItem(Base):
    __tablename__ = "stock_items"
    __table_args__ = (
        UniqueConstraint("warehouse_id", "product_id", name="uq_stock_items_warehouse_product"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    warehouse_id = Column(
        BigInteger, ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id = Column(BigInteger, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    quantity = Column(Numeric(12, 3), nullable=False, default=0, server_default="0")
    reserved = Column(Numeric(12, 3), nullable=False, default=0, server_default="0")
    unit_cost = Column(Numeric(12, 2), nullable=True)
    updated_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    code = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    feed_url = Column(String, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, server_default="true")
    # Импорт сам заводит товары витрины, покупатель видит их в наличии у поставщика
    show_on_storefront = Column(Boolean, nullable=False, default=False, server_default="false")
    last_synced_at = Column(TIMESTAMP(timezone=True), nullable=True)
    # Причина последнего неудачного импорта, пусто после успешного
    last_sync_error = Column(String, nullable=True)
    # Итог последнего успешного импорта: сколько добавлено, обновлено, скрыто
    last_sync_summary = Column(JSONB, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)


class SupplierCategory(Base):
    """Категория из выгрузки поставщика и раздел витрины, куда попадают её товары."""

    __tablename__ = "supplier_categories"
    __table_args__ = (
        UniqueConstraint("supplier_id", "external_id", name="uq_supplier_categories_supplier_external"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    supplier_id = Column(
        BigInteger, ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    external_id = Column(String, nullable=False)
    parent_external_id = Column(String, nullable=True)
    name = Column(String, nullable=False)
    # Пусто, пока импорт не завёл раздел. Менеджер может перенаправить в другой раздел
    category_id = Column(BigInteger, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)


class SupplierOffer(Base):
    __tablename__ = "supplier_offers"
    __table_args__ = (
        UniqueConstraint("supplier_id", "external_id", name="uq_supplier_offers_supplier_external"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    supplier_id = Column(
        BigInteger, ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Пусто, пока предложение не сопоставлено с товаром витрины
    product_id = Column(BigInteger, ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True)
    external_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    url = Column(String, nullable=True)
    # Данные выгрузки для создания товара витрины
    vendor = Column(String, nullable=True)
    category_name = Column(String, nullable=True)
    category_external_id = Column(String, nullable=True)
    picture_url = Column(String, nullable=True)
    weight_kg = Column(Numeric(10, 3), nullable=True)
    # Закупочная цена
    price = Column(Numeric(12, 2), nullable=False)
    quantity = Column(Numeric(12, 3), nullable=False, default=0, server_default="0")
    is_active = Column(Boolean, nullable=False, default=True, server_default="true")
    last_seen_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
