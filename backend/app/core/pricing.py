from decimal import ROUND_CEILING, Decimal


def calc_sale_price(cost: Decimal, markup_percent: Decimal, min_profit: Decimal) -> Decimal:
    """
    Цена продажи товара партнёра.

    Берём большее из наценки в процентах и минимальной прибыли и округляем вверх до рубля:
    дешёвый товар с наценкой 15% не принесёт и пары рублей.
    """
    by_markup = cost * (1 + markup_percent / 100)
    by_profit = cost + min_profit
    return max(by_markup, by_profit).quantize(Decimal("1"), rounding=ROUND_CEILING)


def calc_fixed_price(price: Decimal, cost: Decimal | None, min_profit: Decimal) -> Decimal:
    """
    Цена товара с точной ценой.

    Обычно это сама точная цена. Если закупка выросла и прибыль стала меньше минимальной,
    цена поднимается до закупки плюс минимум, округлённой вверх до рубля. Без закупки
    (товар только со своего склада) сравнивать не с чем.
    """
    if cost is None:
        return price
    floor = (cost + min_profit).quantize(Decimal("1"), rounding=ROUND_CEILING)
    return max(price, floor)
