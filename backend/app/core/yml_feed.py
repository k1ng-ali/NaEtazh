"""
Разбор YML-выгрузки поставщика (формат Яндекс Маркета).
"""

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from xml.etree.ElementTree import Element, ParseError

from defusedxml import DefusedXmlException
from defusedxml.ElementTree import fromstring

# Название магазина партнёра не должно попасть на нашу витрину
_PARTNER_NAME_RE = re.compile(r"[\s,]*\(?\s*фамаркет\s*\)?", re.IGNORECASE)


class FeedError(ValueError):
    pass


@dataclass
class FeedCategory:
    external_id: str
    name: str
    parent_external_id: str | None = None


@dataclass
class FeedOffer:
    external_id: str
    name: str
    price: Decimal
    # count в выгрузке, available="true" у всех и ничего не значит
    quantity: Decimal
    url: str | None = None
    vendor: str | None = None
    category_name: str | None = None
    category_external_id: str | None = None
    picture_url: str | None = None
    weight_kg: Decimal | None = None


@dataclass
class YmlFeed:
    categories: list[FeedCategory]
    offers: list[FeedOffer]


def clean_name(name: str) -> str:
    return " ".join(_PARTNER_NAME_RE.sub(" ", name).split())


def _text(element: Element, tag: str) -> str | None:
    child = element.find(tag)
    value = child.text.strip() if child is not None and child.text else ""
    return value or None


def _decimal(value: str | None) -> Decimal | None:
    if value is None:
        return None
    try:
        number = Decimal(value.replace(",", ".").replace(" ", ""))
    except InvalidOperation:
        return None
    return number if number.is_finite() else None


def parse_yml(content: bytes) -> YmlFeed:
    """Дерево категорий и предложения. Строки без id, названия или цены пропускаются."""
    try:
        root = fromstring(content)
    except (ParseError, DefusedXmlException) as exc:
        raise FeedError("Выгрузка не является корректным XML") from exc

    shop = root.find("shop")
    if shop is None:
        raise FeedError("В выгрузке нет раздела <shop>")

    categories: dict[str, FeedCategory] = {}
    for item in shop.iterfind("categories/category"):
        category_id = (item.get("id") or "").strip()
        name = " ".join((item.text or "").split())
        if category_id and name:
            parent_id = (item.get("parentId") or "").strip() or None
            categories[category_id] = FeedCategory(
                external_id=category_id, name=name[:250], parent_external_id=parent_id
            )
    offers: list[FeedOffer] = []
    for item in shop.iterfind("offers/offer"):
        external_id = (item.get("id") or "").strip()
        name = clean_name(_text(item, "name") or "")
        price = _decimal(_text(item, "price"))
        if not external_id or not name or price is None or price <= 0:
            continue

        quantity = _decimal(_text(item, "count")) or Decimal("0")
        weight = _decimal(_text(item, "weight"))
        category = categories.get(_text(item, "categoryId") or "")
        offers.append(
            FeedOffer(
                external_id=external_id,
                name=name[:250],
                price=price.quantize(Decimal("0.01")),
                # Отрицательный остаток в выгрузке означает «нет в наличии»
                quantity=max(quantity, Decimal("0")).quantize(Decimal("0.001")),
                url=_text(item, "url"),
                # Собственная марка партнёра тоже выдаёт источник
                vendor=clean_name(_text(item, "vendor") or "") or None,
                category_name=category.name if category else None,
                category_external_id=category.external_id if category else None,
                picture_url=_text(item, "picture"),
                weight_kg=weight.quantize(Decimal("0.001")) if weight is not None and weight > 0 else None,
            )
        )
    return YmlFeed(categories=list(categories.values()), offers=offers)
