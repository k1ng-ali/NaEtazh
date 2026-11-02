"""
Правила наценки на товары партнёра.

Правило без категории действует по умолчанию. Правило категории перекрывает его.
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
