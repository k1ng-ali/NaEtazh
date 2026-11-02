import secrets

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.slug import slugify
from app.repositories.location_repo import LocationRepository
from app.schemas.location import (
    BuildingIn,
    BuildingOut,
    BuildingUpdate,
    ComplexIn,
    ComplexOutAdmin,
    ComplexUpdate,
    TariffIn,
    TariffOut,
)

# Без похожих символов: код могут набрать вручную с визитки
CODE_ALPHABET = "abcdefghjkmnpqrstuvwxyz23456789"
CODE_LENGTH = 6


class LocationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = LocationRepository(db=db)

    # ─── Жилые комплексы и корпуса ────────────────────────────────────────────

    async def list_complexes(self) -> list[ComplexOutAdmin]:
        complexes = await self.repo.get_complexes()
        buildings = await self.repo.get_buildings(complex_ids=[item.id for item in complexes])
        return [
            ComplexOutAdmin.model_validate(item).model_copy(
                update={
                    "buildings": [
                        BuildingOut.model_validate(building)
                        for building in buildings
                        if building.complex_id == item.id
                    ]
                }
            )
            for item in complexes
        ]

    async def create_complex(self, data: ComplexIn) -> ComplexOutAdmin:
        slug = data.slug or slugify(data.name)
        if await self.repo.complex_slug_exists(slug=slug):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Complex slug already exists")
        complex_ = await self.repo.create_complex(**data.model_dump(exclude={"slug"}), slug=slug)
        await self.db.commit()
        return ComplexOutAdmin.model_validate(complex_)

    async def update_complex(self, complex_id: int, data: ComplexUpdate) -> ComplexOutAdmin:
        complex_ = await self._get_complex_or_404(complex_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            if value is None and field in ("name", "is_active"):
                continue
            setattr(complex_, field, value)
        await self.db.commit()
        return next(item for item in await self.list_complexes() if item.id == complex_id)

    async def create_building(self, complex_id: int, data: BuildingIn) -> BuildingOut:
        await self._get_complex_or_404(complex_id)
        code = data.code or await self._generate_code()
        if await self.repo.building_code_exists(code=code):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Building code already exists")
        building = await self.repo.create_building(
            complex_id=complex_id, **data.model_dump(exclude={"code"}), code=code
        )
        await self.db.commit()
        return BuildingOut.model_validate(building)

    async def update_building(self, building_id: int, data: BuildingUpdate) -> BuildingOut:
        # Код не меняется: он уже напечатан на визитках
        building = await self.repo.get_building(building_id)
        if building is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Building not found")
        for field, value in data.model_dump(exclude_unset=True).items():
            if value is None and field == "name":
                continue
            setattr(building, field, value)
        await self.db.commit()
        return BuildingOut.model_validate(building)

    # ─── Тарифы ───────────────────────────────────────────────────────────────

    async def list_tariffs(self) -> list[TariffOut]:
        return [TariffOut.model_validate(item) for item in await self.repo.get_tariffs()]

    async def save_tariff(self, data: TariffIn) -> TariffOut:
        if data.complex_id is not None:
            await self._get_complex_or_404(data.complex_id)
        tariff = await self.repo.get_tariff_by_complex_for_update(complex_id=data.complex_id)
        if tariff is None:
            tariff = await self.repo.create_tariff(**data.model_dump())
        else:
            for field, value in data.model_dump(exclude={"complex_id"}).items():
                setattr(tariff, field, value)
        await self.db.commit()
        await self.db.refresh(tariff)
        return TariffOut.model_validate(tariff)

    async def delete_tariff(self, tariff_id: int) -> None:
        tariff = await self.repo.get_tariff(tariff_id)
        if tariff is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tariff not found")
        await self.repo.delete_tariff(tariff)
        await self.db.commit()

    # ─── Хелперы ──────────────────────────────────────────────────────────────

    async def _get_complex_or_404(self, complex_id: int):
        complex_ = await self.repo.get_complex(complex_id)
        if complex_ is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complex not found")
        return complex_

    async def _generate_code(self) -> str:
        while True:
            code = "".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH))
            if not await self.repo.building_code_exists(code=code):
                return code
