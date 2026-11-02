from fastapi import APIRouter, Depends, status

from app.deps.auth import require_admin, require_staff
from app.deps.services import get_location_service
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
from app.services.location_service import LocationService

router = APIRouter(tags=["Admin • Locations"])


# ─── Жилые комплексы и корпуса ────────────────────────────────────────────────


@router.get("/complexes/", response_model=list[ComplexOutAdmin], dependencies=[Depends(require_staff)])
async def list_complexes(service: LocationService = Depends(get_location_service)):
    return await service.list_complexes()


@router.post(
    "/complexes/",
    response_model=ComplexOutAdmin,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_staff)],
)
async def create_complex(data: ComplexIn, service: LocationService = Depends(get_location_service)):
    return await service.create_complex(data=data)


@router.patch(
    "/complexes/{complex_id}", response_model=ComplexOutAdmin, dependencies=[Depends(require_staff)]
)
async def update_complex(
    complex_id: int, data: ComplexUpdate, service: LocationService = Depends(get_location_service)
):
    return await service.update_complex(complex_id=complex_id, data=data)


@router.post(
    "/complexes/{complex_id}/buildings",
    response_model=BuildingOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_staff)],
)
async def create_building(
    complex_id: int, data: BuildingIn, service: LocationService = Depends(get_location_service)
):
    return await service.create_building(complex_id=complex_id, data=data)


@router.patch("/buildings/{building_id}", response_model=BuildingOut, dependencies=[Depends(require_staff)])
async def update_building(
    building_id: int, data: BuildingUpdate, service: LocationService = Depends(get_location_service)
):
    return await service.update_building(building_id=building_id, data=data)


# ─── Тарифы ───────────────────────────────────────────────────────────────────


@router.get("/tariffs/", response_model=list[TariffOut], dependencies=[Depends(require_staff)])
async def list_tariffs(service: LocationService = Depends(get_location_service)):
    return await service.list_tariffs()


# Тарифы влияют на выручку, поэтому их меняет администратор
@router.put("/tariffs/", response_model=TariffOut, dependencies=[Depends(require_admin)])
async def save_tariff(data: TariffIn, service: LocationService = Depends(get_location_service)):
    return await service.save_tariff(data=data)


@router.delete(
    "/tariffs/{tariff_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin)]
)
async def delete_tariff(tariff_id: int, service: LocationService = Depends(get_location_service)):
    await service.delete_tariff(tariff_id=tariff_id)
