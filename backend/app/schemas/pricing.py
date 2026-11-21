from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class PricingRuleIn(BaseModel):
    # Пусто: правило по умолчанию
    category_id: int | None = None
    markup_percent: Decimal = Field(ge=0, le=500, max_digits=6, decimal_places=2)
    min_profit: Decimal = Field(Decimal("0"), ge=0, max_digits=12, decimal_places=2)


class PricingRuleOut(BaseModel):
    id: int
    category_id: int | None = None
    markup_percent: Decimal
    min_profit: Decimal
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PricingRuleSaveOut(BaseModel):
    rule: PricingRuleOut
    # Сколько цен изменилось после сохранения
    updated_prices: int


class ProductPriceIn(BaseModel):
    product_id: int
    # Точная цена продажи
    price: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    # Прибыль с единицы не меньше этой суммы, даже если закупка вырастет
    min_profit: Decimal = Field(Decimal("0"), ge=0, max_digits=12, decimal_places=2)


class ProductPriceOut(BaseModel):
    product_id: int
    product_name: str
    product_sku: str
    price: Decimal
    min_profit: Decimal
    # Цена на витрине сейчас: точная или поднятая из-за закупки
    sale_price: Decimal
    # Закупка у партнёра, от которой считается минимум. Пусто, если предложения нет
    cost: Decimal | None = None
    # Менеджер поставил цену вручную, точная цена не действует
    is_price_manual: bool
    updated_at: datetime
