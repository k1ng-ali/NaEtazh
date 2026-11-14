from sqlalchemy import func, select

from app.models.location import Building, ResidentialComplex
from app.models.service import ServiceRequest, ShopService, ShopSettings
from app.repositories.base_repo import BaseRepository


class ServiceRepository(BaseRepository):

    # ─── Услуги ───────────────────────────────────────────────────────────────

    async def get_services(self, active_only: bool) -> list[ShopService]:
        query = select(ShopService).order_by(ShopService.position, ShopService.id)
        if active_only:
            query = query.where(ShopService.is_active == True)  # noqa: E712
        return list((await self.db.execute(query)).scalars().all())

    async def get_active_service_by_slug(self, slug: str) -> ShopService | None:
        result = await self.db.execute(
            select(ShopService).where(ShopService.slug == slug, ShopService.is_active == True)  # noqa: E712
        )
        return result.scalar_one_or_none()

    async def get_service(self, service_id: int) -> ShopService | None:
        return await self.db.get(ShopService, service_id)

    async def get_service_slugs(self) -> set[str]:
        return set((await self.db.execute(select(ShopService.slug))).scalars().all())

    async def get_settings(self) -> ShopSettings:
        settings = await self.db.get(ShopSettings, 1)
        if settings is None:
            # Строку создаёт миграция, это на случай ручной очистки таблицы
            settings = ShopSettings(id=1)
            await self.add(settings)
        return settings

    async def add(self, item) -> None:
        self.db.add(item)
        await self.db.flush()

    # ─── Заявки ───────────────────────────────────────────────────────────────

    @staticmethod
    def _with_location():
        return (
            select(ServiceRequest, Building, ResidentialComplex)
            .outerjoin(Building, Building.id == ServiceRequest.building_id)
            .outerjoin(ResidentialComplex, ResidentialComplex.id == Building.complex_id)
        )

    async def get_requests(
        self, status: str | None, skip: int, limit: int
    ) -> tuple[list[tuple[ServiceRequest, Building | None, ResidentialComplex | None]], int]:
        conditions = [ServiceRequest.status == status] if status else []
        total = await self.db.scalar(select(func.count(ServiceRequest.id)).where(*conditions))
        result = await self.db.execute(
            self._with_location()
            .where(*conditions)
            .order_by(ServiceRequest.created_at.desc(), ServiceRequest.id.desc())
            .offset(skip)
            .limit(limit)
        )
        return [tuple(row) for row in result.all()], total or 0

    async def get_request(self, request_id: int) -> ServiceRequest | None:
        return await self.db.get(ServiceRequest, request_id)

    async def get_request_with_location(
        self, request_id: int
    ) -> tuple[ServiceRequest, Building | None, ResidentialComplex | None] | None:
        row = (await self.db.execute(self._with_location().where(ServiceRequest.id == request_id))).first()
        return tuple(row) if row else None
