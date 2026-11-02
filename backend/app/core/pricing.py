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
