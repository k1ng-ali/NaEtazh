"""
Модели заказа.

- Order: заказ покупателя, public_token открывает страницу статуса
- OrderLine: снимок товара и цены на момент заказа
- OrderAllocation: откуда взято количество и за какую себестоимость
- OrderServiceLine: доставка или подъём, цена и расход
"""

from sqlalchemy import TIMESTAMP, BigInteger, Column, Date, ForeignKey, Numeric, String, Text, func

from app.core.database import Base
from app.enums.order import LiftingTypeEnum, OrderStatusEnum


class Order(Base):
    __tablename__ = "orders"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    public_token = Column(String, nullable=False, unique=True)
    status = Column(
        String,
        nullable=False,
        default=OrderStatusEnum.new.value,
        server_default=OrderStatusEnum.new.value,
        index=True,
    )
    building_id = Column(
        BigInteger, ForeignKey("buildings.id", ondelete="SET NULL"), nullable=True, index=True
    )
    # Адрес вне подключённых домов
    address_text = Column(String, nullable=True)
    entrance = Column(String, nullable=True)
    floor = Column(String, nullable=True)
    apartment = Column(String, nullable=True)
    customer_name = Column(String, nullable=False)
    customer_phone = Column(String, nullable=False)
    contact_channel = Column(String, nullable=True)
    missing_item_policy = Column(String, nullable=True)
    comment = Column(Text, nullable=True)
    lifting_type = Column(
        String,
        nullable=False,
        default=LiftingTypeEnum.none.value,
        server_default=LiftingTypeEnum.none.value,
    )
    # Пожелание покупателя, менеджер подтверждает по телефону
    delivery_date = Column(Date, nullable=True)
    delivery_slot = Column(String, nullable=True)
    # Метка QR-кода или партии визиток
    source_code = Column(String, nullable=True, index=True)
    goods_total = Column(Numeric(12, 2), nullable=False)
    services_total = Column(Numeric(12, 2), nullable=False, default=0, server_default="0")
    total = Column(Numeric(12, 2), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class OrderLine(Base):
    __tablename__ = "order_lines"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    order_id = Column(BigInteger, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(
        BigInteger, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    name = Column(String, nullable=False)
    unit = Column(String, nullable=False)
    quantity = Column(Numeric(12, 3), nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)
    total = Column(Numeric(12, 2), nullable=False)


class OrderAllocation(Base):
    __tablename__ = "order_allocations"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    order_line_id = Column(
        BigInteger, ForeignKey("order_lines.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_type = Column(String, nullable=False)
    warehouse_id = Column(
        BigInteger, ForeignKey("warehouses.id", ondelete="SET NULL"), nullable=True, index=True
    )
    supplier_offer_id = Column(
        BigInteger,
        ForeignKey("supplier_offers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    quantity = Column(Numeric(12, 3), nullable=False)
    unit_cost = Column(Numeric(12, 2), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)


class OrderServiceLine(Base):
    __tablename__ = "order_service_lines"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    order_id = Column(BigInteger, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String, nullable=False)
    name = Column(String, nullable=False)
    price = Column(Numeric(12, 2), nullable=False)
    # Расход клиента на услугу, для расчёта прибыли
    cost = Column(Numeric(12, 2), nullable=True)
