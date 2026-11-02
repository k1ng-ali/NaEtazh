from sqlalchemy import select

from app.models.location import Building, ResidentialComplex, ServiceTariff
from app.repositories.base_repo import BaseRepository


class LocationRepository(BaseRepository):

    # ─── Корпуса ──────────────────────────────────────────────────────────────

    async def get_building_by_code(self, code: str) -> tuple[Building, ResidentialComplex] | None:
        result = await self.db.execute(
            select(Building, ResidentialComplex)
            .join(ResidentialComplex, ResidentialComplex.id == Building.complex_id)
            .where(Building.code == code, ResidentialComplex.is_active == True)  # noqa: E712
        )
        row = result.first()
        return (row[0], row[1]) if row else None

    async def get_buildings_with_complexes(
        self, building_ids: list[int]
    ) -> dict[int, tuple[Building, ResidentialComplex]]:
        if not building_ids:
            return {}
        result = await self.db.execute(
            select(Building, ResidentialComplex)
            .join(ResidentialComplex, ResidentialComplex.id == Building.complex_id)
            .where(Building.id.in_(building_ids))
        )
        return {building.id: (building, complex_) for building, complex_ in result.all()}

    async def get_complexes(self) -> list[ResidentialComplex]:
        result = await self.db.execute(select(ResidentialComplex).order_by(ResidentialComplex.name))
        return list(result.scalars().all())

    async def get_complex(self, complex_id: int) -> ResidentialComplex | None:
        return await self.db.get(ResidentialComplex, complex_id)

    async def get_buildings(self, complex_ids: list[int]) -> list[Building]:
        if not complex_ids:
            return []
        result = await self.db.execute(
            select(Building).where(Building.complex_id.in_(complex_ids)).order_by(Building.name)
        )
        return list(result.scalars().all())

    async def get_building(self, building_id: int) -> Building | None:
        return await self.db.get(Building, building_id)

    async def complex_slug_exists(self, slug: str) -> bool:
        result = await self.db.execute(select(ResidentialComplex.id).where(ResidentialComplex.slug == slug))
        return result.scalar() is not None

    async def building_code_exists(self, code: str) -> bool:
        result = await self.db.execute(select(Building.id).where(Building.code == code))
        return result.scalar() is not None

    async def create_complex(self, **values) -> ResidentialComplex:
        complex_ = ResidentialComplex(**values)
        self.db.add(complex_)
        await self.db.flush()
        await self.db.refresh(complex_)
        return complex_

    async def create_building(self, **values) -> Building:
        building = Building(**values)
        self.db.add(building)
        await self.db.flush()
        await self.db.refresh(building)
        return building

    # ─── Тарифы ───────────────────────────────────────────────────────────────

    async def get_tariffs(self) -> list[ServiceTariff]:
        result = await self.db.execute(
            select(ServiceTariff).order_by(ServiceTariff.complex_id.is_not(None), ServiceTariff.id)
        )
        return list(result.scalars().all())

    async def get_tariff(self, tariff_id: int) -> ServiceTariff | None:
        return await self.db.get(ServiceTariff, tariff_id)

    async def get_effective_tariff(self, complex_id: int | None) -> ServiceTariff | None:
        """Тариф комплекса, а если его нет — тариф по умолчанию."""
        condition = ServiceTariff.complex_id.is_(None)
        if complex_id is not None:
            condition = condition | (ServiceTariff.complex_id == complex_id)
        result = await self.db.execute(
            select(ServiceTariff).where(condition).order_by(ServiceTariff.complex_id.is_(None)).limit(1)
        )
        return result.scalar_one_or_none()

    async def get_tariff_by_complex_for_update(self, complex_id: int | None) -> ServiceTariff | None:
        condition = (
            ServiceTariff.complex_id.is_(None)
            if complex_id is None
            else ServiceTariff.complex_id == complex_id
        )
        result = await self.db.execute(select(ServiceTariff).where(condition).with_for_update())
        return result.scalar_one_or_none()

    async def create_tariff(self, **values) -> ServiceTariff:
        tariff = ServiceTariff(**values)
        self.db.add(tariff)
        await self.db.flush()
        await self.db.refresh(tariff)
        return tariff

    async def delete_tariff(self, tariff: ServiceTariff) -> None:
        await self.db.delete(tariff)
        await self.db.flush()
