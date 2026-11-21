"""
Правила наценки на товары партнёра.

Правило без категории действует по умолчанию. Правило категории перекрывает его,
а точная цена товара (ProductPrice) — любое правило.
"""

from sqlalchemy import TIMESTAMP, BigInteger, Column, ForeignKey, Numeric, UniqueConstraint, func

from app.core.database import Base


class PricingRule(Base):
    __tablename__ = "pricing_rules"
    __table_args__ = (UniqueConstraint("category_id", name="uq_pricing_rules_category"),)

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    # Пусто у правила по умолчанию, единственность проверяет сервис
    category_id = Column(BigInteger, ForeignKey("categories.id", ondelete="CASCADE"), nullable=True)
    markup_percent = Column(Numeric(6, 2), nullable=False)
    # Прибыль с единицы не меньше этой суммы
    min_profit = Column(Numeric(12, 2), nullable=False, default=0, server_default="0")
    updated_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class ProductPrice(Base):
    """
    Точная цена продажи товара вместо наценки.

    Если закупка у партнёра вырастет и прибыль станет меньше min_profit, пересчёт поднимет
    цену до закупки плюс min_profit. Когда закупка снова упадёт, цена вернётся к точной.
    """

    __tablename__ = "product_prices"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    product_id = Column(
        BigInteger, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    price = Column(Numeric(12, 2), nullable=False)
    min_profit = Column(Numeric(12, 2), nullable=False, default=0, server_default="0")
    updated_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
