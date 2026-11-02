from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock

from app.core.pricing import calc_sale_price
from app.services.pricing_service import PricingService


def test_calc_sale_price_uses_markup():
    assert calc_sale_price(Decimal("1150"), Decimal("20"), Decimal("30")) == Decimal("1380")


def test_calc_sale_price_uses_min_profit_for_cheap_items():
    assert calc_sale_price(Decimal("50"), Decimal("20"), Decimal("30")) == Decimal("80")


def test_calc_sale_price_rounds_up_to_ruble():
    assert calc_sale_price(Decimal("99.10"), Decimal("10"), Decimal("0")) == Decimal("110")


async def test_recalc_prices_prefers_category_rule_and_keeps_price_without_offer():
    service = PricingService(db=AsyncMock())
    with_offer = SimpleNamespace(id=1, category_id=7, price=Decimal("1"))
    without_offer = SimpleNamespace(id=2, category_id=7, price=Decimal("500"))
    service.repo.get_auto_priced_products = AsyncMock(return_value=[with_offer, without_offer])
    service.repo.get_best_offers = AsyncMock(return_value={1: SimpleNamespace(price=Decimal("100"))})
    service.repo.get_rules = AsyncMock(
        return_value=[
            SimpleNamespace(category_id=None, markup_percent=Decimal("20"), min_profit=Decimal("0")),
            SimpleNamespace(category_id=7, markup_percent=Decimal("50"), min_profit=Decimal("0")),
        ]
    )

    updated = await service.recalc_prices()

    assert updated == 1
    assert with_offer.price == Decimal("150")
    assert without_offer.price == Decimal("500")
