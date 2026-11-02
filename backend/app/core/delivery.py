"""
Расчёт цены доставки и подъёма по тарифу.
"""

from decimal import ROUND_CEILING, Decimal

from app.enums.order import LiftingTypeEnum

HUNDRED = Decimal("100")


def calc_delivery_price(goods_total: Decimal, price: Decimal, free_from: Decimal | None) -> Decimal:
    if free_from is not None and goods_total >= free_from:
        return Decimal("0")
    return price


def _hundreds(weight_kg: Decimal) -> Decimal:
    """Число начатых сотен килограммов: 101 кг считаем как 200."""
    if weight_kg <= 0:
        return Decimal("0")
    return (weight_kg / HUNDRED).quantize(Decimal("1"), rounding=ROUND_CEILING)


def calc_lifting_price(
    lifting_type: LiftingTypeEnum,
    weight_kg: Decimal,
    floor: int | None,
    lift_price_per_100kg: Decimal,
    lift_min_price: Decimal,
    stairs_price_per_100kg_floor: Decimal,
) -> Decimal:
    if lifting_type == LiftingTypeEnum.none:
        return Decimal("0")
    hundreds = _hundreds(weight_kg)
    if lifting_type == LiftingTypeEnum.lift:
        return max(hundreds * lift_price_per_100kg, lift_min_price)
    # Первый этаж считаем за один: груз всё равно заносят в квартиру
    floors = max(floor or 1, 1)
    return max(hundreds * stairs_price_per_100kg_floor * floors, lift_min_price)
