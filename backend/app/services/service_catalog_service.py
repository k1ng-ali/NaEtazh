from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.slug import slugify
from app.models.location import Building, ResidentialComplex
from app.models.service import ServiceRequest, ShopService
from app.repositories.location_repo import LocationRepository
from app.repositories.service_repo import ServiceRepository
from app.schemas.service import (
    ServiceRequestCreatedOut,
    ServiceRequestCreateIn,
    ServiceRequestListOut,
    ServiceRequestOut,
    ShopContactsIn,
    ShopContactsOut,
    ShopServiceAdminOut,
    ShopServiceIn,
    ShopServiceOut,
)


def format_request_address(
    request: ServiceRequest, building: Building | None, complex_: ResidentialComplex | None
) -> str:
    """«ЖК Северный, корпус 2, кв. 45» или адрес текстом."""
    parts = (
        [complex_.name, building.name]
        if building and complex_
        else [request.address_text or "Адрес не указан"]
    )
    if request.apartment:
        parts.append(f"кв. {request.apartment}")
    return ", ".join(parts)


class ServiceCatalogService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ServiceRepository(db=db)

    # ─── Витрина ──────────────────────────────────────────────────────────────

    async def list_services(self) -> list[ShopServiceOut]:
        phone = (await self.repo.get_settings()).phone
        return [self._public_out(item, phone) for item in await self.repo.get_services(active_only=True)]

    async def get_service(self, slug: str) -> ShopServiceOut:
        service = await self._get_active_or_404(slug)
        return self._public_out(service, (await self.repo.get_settings()).phone)

    async def get_contacts(self) -> ShopContactsOut:
        return ShopContactsOut(phone=(await self.repo.get_settings()).phone)

    async def create_request(self, data: ServiceRequestCreateIn) -> tuple[ServiceRequestCreatedOut, str]:
        """Номер заявки и текст уведомления менеджеру."""
        service = await self._get_active_or_404(data.service_slug)
        row = (
            await LocationRepository(db=self.db).get_building_by_code(code=data.building_code.lower())
            if data.building_code
            else None
        )
        building, complex_ = row if row else (None, None)
        address_text = data.address_text.strip() if data.address_text else None
        if building is None and not address_text:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Address is required"
            )
        if data.preferred_date and data.preferred_date < date.today():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Date is in the past"
            )

        request = ServiceRequest(
            service_id=service.id,
            service_name=service.name,
            customer_name=data.customer_name.strip(),
            customer_phone=data.customer_phone,
            building_id=building.id if building else None,
            address_text=None if building else address_text,
            apartment=data.apartment.strip() if data.apartment else None,
            preferred_date=data.preferred_date,
            comment=data.comment.strip() if data.comment else None,
            source_code=data.source_code,
        )
        await self.repo.add(request)
        await self.db.commit()
        return ServiceRequestCreatedOut(number=request.id), self._notification_text(
            request, format_request_address(request, building, complex_)
        )

    # ─── Заявки для менеджера ─────────────────────────────────────────────────

    async def list_requests(self, status: str | None, skip: int, limit: int) -> ServiceRequestListOut:
        rows, total = await self.repo.get_requests(status=status, skip=skip, limit=limit)
        return ServiceRequestListOut(
            items=[self._request_out(request, building, complex_) for request, building, complex_ in rows],
            total=total,
        )

    async def set_request_status(self, request_id: int, new_status: str) -> ServiceRequestOut:
        request = await self.repo.get_request(request_id)
        if request is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
        request.status = new_status
        await self.db.commit()
        return self._request_out(*await self.repo.get_request_with_location(request_id))

    # ─── Справочник для владельца ─────────────────────────────────────────────

    async def list_services_admin(self) -> list[ShopServiceAdminOut]:
        return [
            ShopServiceAdminOut.model_validate(item)
            for item in await self.repo.get_services(active_only=False)
        ]

    async def create_service(self, data: ShopServiceIn) -> ShopServiceAdminOut:
        slug, suffix, taken = slugify(data.name), 2, await self.repo.get_service_slugs()
        base = slug
        while slug in taken:
            slug, suffix = f"{base}-{suffix}", suffix + 1
        service = ShopService(slug=slug, **data.model_dump())
        await self.repo.add(service)
        await self.db.commit()
        await self.db.refresh(service)
        return ShopServiceAdminOut.model_validate(service)

    async def update_service(self, service_id: int, data: ShopServiceIn) -> ShopServiceAdminOut:
        # Адрес страницы не меняем при переименовании: ссылки уже могли разойтись
        service = await self.repo.get_service(service_id)
        if service is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
        for field, value in data.model_dump().items():
            setattr(service, field, value)
        await self.db.commit()
        await self.db.refresh(service)
        return ShopServiceAdminOut.model_validate(service)

    async def set_contacts(self, data: ShopContactsIn) -> ShopContactsOut:
        settings = await self.repo.get_settings()
        settings.phone = data.phone
        await self.db.commit()
        return ShopContactsOut(phone=settings.phone)

    # ─── Хелперы ──────────────────────────────────────────────────────────────

    async def _get_active_or_404(self, slug: str) -> ShopService:
        service = await self.repo.get_active_service_by_slug(slug)
        if service is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
        return service

    @staticmethod
    def _public_out(service: ShopService, general_phone: str | None) -> ShopServiceOut:
        return ShopServiceOut.model_validate(service).model_copy(
            update={"phone": service.phone or general_phone}
        )

    @staticmethod
    def _request_out(
        request: ServiceRequest, building: Building | None, complex_: ResidentialComplex | None
    ) -> ServiceRequestOut:
        return ServiceRequestOut(
            id=request.id,
            service_name=request.service_name,
            status=request.status,
            customer_name=request.customer_name,
            customer_phone=request.customer_phone,
            address=format_request_address(request, building, complex_),
            preferred_date=request.preferred_date,
            comment=request.comment,
            created_at=request.created_at,
        )

    @staticmethod
    def _notification_text(request: ServiceRequest, address: str) -> str:
        # Имя и телефон в Telegram не отправляем, как и в заказах: серверы за рубежом
        lines = [f"Заявка на услугу № {request.id}: {request.service_name}", address]
        if request.preferred_date:
            lines.append(f"Когда удобно: {request.preferred_date:%d.%m}")
        lines.append(f"{settings.SITE_URL}/manager/requests")
        return "\n".join(lines)
