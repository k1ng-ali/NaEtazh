from decimal import Decimal

import pytest

from app.core.yml_feed import FeedError, clean_name, parse_yml

FEED = """<?xml version="1.0" encoding="windows-1251"?>
<yml_catalog date="2026-11-02 10:00">
  <shop>
    <categories>
      <category id="4">Общестроительные материалы</category>
      <category id="418" parentId="4">Газобетон</category>
      <category id="">Без id</category>
    </categories>
    <offers>
      <offer id="00-1" available="true">
        <url>https://famarket.ru/id/1.html</url>
        <price>142</price>
        <weight>15.75</weight>
        <categoryId>418</categoryId>
        <picture>https://famarket.ru/1.jpg</picture>
        <picture>https://famarket.ru/2.jpg</picture>
        <name>Газобетонный блок D-500 (Фамаркет)</name>
        <vendor>ФаМаркет</vendor>
        <count>1304</count>
      </offer>
      <offer id="00-2" available="true">
        <price>99,5</price>
        <name>Сетка малярная</name>
        <count>-3</count>
      </offer>
      <offer id="00-3" available="true">
        <price>0</price>
        <name>Без цены</name>
      </offer>
      <offer available="true">
        <price>10</price>
        <name>Без id</name>
      </offer>
    </offers>
  </shop>
</yml_catalog>
""".encode("cp1251")


def test_parse_yml_reads_offers_in_cp1251():
    offers = parse_yml(FEED).offers

    assert [offer.external_id for offer in offers] == ["00-1", "00-2"]
    first = offers[0]
    assert first.name == "Газобетонный блок D-500"
    assert first.vendor is None
    assert first.category_name == "Газобетон"
    assert first.category_external_id == "418"
    assert first.picture_url == "https://famarket.ru/1.jpg"
    assert first.price == Decimal("142.00")
    assert first.quantity == Decimal("1304.000")
    assert first.weight_kg == Decimal("15.750")


def test_parse_yml_reads_category_tree():
    categories = parse_yml(FEED).categories

    assert [(c.external_id, c.parent_external_id, c.name) for c in categories] == [
        ("4", None, "Общестроительные материалы"),
        ("418", "4", "Газобетон"),
    ]


def test_parse_yml_negative_count_is_zero():
    offers = parse_yml(FEED).offers

    assert offers[1].price == Decimal("99.50")
    assert offers[1].quantity == Decimal("0")


def test_parse_yml_invalid_xml():
    with pytest.raises(FeedError):
        parse_yml(b"<html>502 Bad Gateway")


def test_parse_yml_rejects_entities():
    bomb = (
        b'<?xml version="1.0"?><!DOCTYPE x [<!ENTITY a "aaaa">]><yml_catalog><shop>&a;</shop></yml_catalog>'
    )

    with pytest.raises(FeedError):
        parse_yml(bomb)


def test_clean_name_removes_partner_name():
    assert clean_name("Профиль ПН 27х28, Фамаркет") == "Профиль ПН 27х28"
    assert clean_name("ФАМАРКЕТ") == ""
