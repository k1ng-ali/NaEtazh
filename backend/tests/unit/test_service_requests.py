from datetime import date, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.schemas.service import ServiceRequestCreateIn, ShopServiceIn
from app.services.service_catalog_service import ServiceCatalogService, format_request_address

SERVICE = SimpleNamespace(id=3, name="Вынос мусора", slug="vynos-musora")


def make_request(**overrides) -> ServiceRequestCreateIn:
    values = {
        "service_slug": "vynos-musora",
        "customer_name": " Анна ",
        "customer_phone": "8 (912) 345-67-89",
        "address_text": "ул. Ленина, 5",
        "apartment": "45",
        "consent": True,
    }
    return ServiceRequestCreateIn(**{**values, **overrides})


def make_service():
    db = AsyncMock()
    service = ServiceCatalogService(db=db)
    service.repo.get_active_service_by_slug = AsyncMock(return_value=SERVICE)

    async def add(item):
        item.id = 17

    service.repo.add = AsyncMock(side_effect=add)
    return service


def test_request_requires_consent_and_valid_phone():
    with pytest.raises(ValidationError):
        make_request(consent=False)
    with pytest.raises(ValidationError):
        make_request(customer_phone="123")
    assert make_request().customer_phone == "+79123456789"


async def test_create_request_saves_and_hides_personal_data_in_notification():
    service = make_service()

    created, text = await service.create_request(make_request(preferred_date=date.today()))

    assert created.number == 17
    saved = service.repo.add.call_args.args[0]
    assert saved.service_name == "Вынос мусора"
    assert saved.customer_name == "Анна"
    assert saved.address_text == "ул. Ленина, 5"
    assert "Заявка на услугу № 17: Вынос мусора" in text
    assert "ул. Ленина, 5, кв. 45" in text
    assert "Анна" not in text and "912" not in text


async def test_create_request_needs_address_and_future_date():
    service = make_service()

    with pytest.raises(HTTPException) as no_address:
        await service.create_request(make_request(address_text="  "))
    with pytest.raises(HTTPException) as past:
        await service.create_request(make_request(preferred_date=date.today() - timedelta(days=1)))

    assert no_address.value.status_code == past.value.status_code == 422
    service.repo.add.assert_not_called()


async def test_create_request_for_hidden_service_is_404():
    service = make_service()
    service.repo.get_active_service_by_slug = AsyncMock(return_value=None)

    with pytest.raises(HTTPException) as exc:
        await service.create_request(make_request())

    assert exc.value.status_code == 404


def test_address_uses_building_from_qr():
    request = SimpleNamespace(address_text=None, apartment="12")
    building = SimpleNamespace(name="корпус 2")
    complex_ = SimpleNamespace(name="ЖК Северный")

    assert format_request_address(request, building, complex_) == "ЖК Северный, корпус 2, кв. 12"


async def test_create_service_gets_unique_slug():
    db = AsyncMock()
    db.refresh = AsyncMock()
    service = ServiceCatalogService(db=db)
    service.repo.get_service_slugs = AsyncMock(return_value={"demontazh"})
    added = []

    async def add(item):
        item.id = 9
        added.append(item)

    service.repo.add = AsyncMock(side_effect=add)
    db.add = MagicMock()

    result = await service.create_service(ShopServiceIn(name="Демонтаж", price_text=" от 500 ₽ ", position=5))

    assert added[0].slug == "demontazh-2"
    assert result.price_text == "от 500 ₽"


def test_display_phone_accepts_landline_and_8800():
    from app.core.phone import clean_display_phone

    assert clean_display_phone("  +7 (3452)  50-50-50 ") == "+7 (3452) 50-50-50"
    assert clean_display_phone("8 800 555-35-35") == "8 800 555-35-35"
    assert clean_display_phone("") is None
    for bad in ("12345", "звоните", "+7 912 345-67-89 доб. 2"):
        with pytest.raises(ValueError):
            clean_display_phone(bad)


def test_public_service_uses_own_phone_or_general():
    def make(phone):
        return SimpleNamespace(
            slug="demontazh", name="Демонтаж", summary=None, description=None, price_text=None, phone=phone
        )

    own = ServiceCatalogService._public_out(make("+7 900 111-22-33"), "+7 3452 50-50-50")
    general = ServiceCatalogService._public_out(make(None), "+7 3452 50-50-50")

    assert own.phone == "+7 900 111-22-33"
    assert general.phone == "+7 3452 50-50-50"
