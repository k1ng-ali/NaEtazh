from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock

from app.core.pricing import calc_fixed_price, calc_sale_price
from app.schemas.pricing import ProductPriceIn
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
    service.repo.get_product_prices = AsyncMock(return_value={})
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


def test_calc_fixed_price_keeps_exact_price():
    assert calc_fixed_price(Decimal("654"), Decimal("500"), Decimal("50")) == Decimal("654")


def test_calc_fixed_price_raises_when_cost_eats_profit():
    # Закупка выросла до 620: при минимуме 50 продаём не дешевле 670
    assert calc_fixed_price(Decimal("654"), Decimal("620"), Decimal("50")) == Decimal("670")


def test_calc_fixed_price_rounds_floor_up_to_ruble():
    assert calc_fixed_price(Decimal("100"), Decimal("99.10"), Decimal("5")) == Decimal("105")


def test_calc_fixed_price_without_cost():
    assert calc_fixed_price(Decimal("654.50"), None, Decimal("50")) == Decimal("654.50")


async def test_recalc_prices_fixed_price_beats_rule_and_works_without_offer():
    service = PricingService(db=AsyncMock())
    fixed = SimpleNamespace(id=1, category_id=7, price=Decimal("1"))
    raised = SimpleNamespace(id=2, category_id=7, price=Decimal("1"))
    own_stock = SimpleNamespace(id=3, category_id=7, price=Decimal("1"))
    service.repo.get_auto_priced_products = AsyncMock(return_value=[fixed, raised, own_stock])
    service.repo.get_best_offers = AsyncMock(
        return_value={1: SimpleNamespace(price=Decimal("100")), 2: SimpleNamespace(price=Decimal("300"))}
    )
    service.repo.get_product_prices = AsyncMock(
        return_value={
            1: SimpleNamespace(price=Decimal("250"), min_profit=Decimal("50")),
            2: SimpleNamespace(price=Decimal("250"), min_profit=Decimal("50")),
            3: SimpleNamespace(price=Decimal("400"), min_profit=Decimal("50")),
        }
    )
    service.repo.get_rules = AsyncMock(
        return_value=[
            SimpleNamespace(category_id=None, markup_percent=Decimal("20"), min_profit=Decimal("0"))
        ]
    )

    updated = await service.recalc_prices()

    assert updated == 3
    assert fixed.price == Decimal("250")
    assert raised.price == Decimal("350")
    assert own_stock.price == Decimal("400")


async def test_save_product_price_switches_product_to_auto_price():
    db = AsyncMock()
    product = SimpleNamespace(id=5, name="Ротбанд", sku="FA-1", price=Decimal("500"), is_price_manual=True)
    db.get = AsyncMock(return_value=product)
    db.add = lambda row: None
    service = PricingService(db=db)
    service.repo.get_product_price_for_update = AsyncMock(return_value=None)
    service.repo.create_product_price = AsyncMock(
        return_value=SimpleNamespace(
            price=Decimal("600"), min_profit=Decimal("50"), updated_at="2026-11-21T00:00:00Z"
        )
    )
    service.recalc_prices = AsyncMock(return_value=1)
    service.repo.get_best_offers = AsyncMock(return_value={5: SimpleNamespace(price=Decimal("400"))})

    result = await service.save_product_price(
        ProductPriceIn(product_id=5, price=Decimal("600"), min_profit=Decimal("50"))
    )

    assert product.is_price_manual is False
    service.recalc_prices.assert_awaited_once_with(product_ids=[5])
    db.commit.assert_awaited_once()
    assert result.cost == Decimal("400")
