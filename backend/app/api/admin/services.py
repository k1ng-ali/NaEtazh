from fastapi import APIRouter, Depends, status

from app.deps.auth import require_admin
from app.deps.services import get_service_catalog_service
from app.schemas.service import ShopContactsIn, ShopContactsOut, ShopServiceAdminOut, ShopServiceIn
from app.services.service_catalog_service import ServiceCatalogService

# Цены услуг задаёт владелец
router = APIRouter(prefix="/services", tags=["Admin • Services"], dependencies=[Depends(require_admin)])


@router.get("/", response_model=list[ShopServiceAdminOut])
async def list_services(service: ServiceCatalogService = Depends(get_service_catalog_service)):
    return await service.list_services_admin()


@router.get("/contacts", response_model=ShopContactsOut)
async def get_contacts(service: ServiceCatalogService = Depends(get_service_catalog_service)):
    return await service.get_contacts()


@router.put("/contacts", response_model=ShopContactsOut)
async def set_contacts(
    data: ShopContactsIn, service: ServiceCatalogService = Depends(get_service_catalog_service)
):
    return await service.set_contacts(data=data)


@router.post("/", response_model=ShopServiceAdminOut, status_code=status.HTTP_201_CREATED)
async def create_service(
    data: ShopServiceIn, service: ServiceCatalogService = Depends(get_service_catalog_service)
):
    return await service.create_service(data=data)


@router.put("/{service_id}", response_model=ShopServiceAdminOut)
async def update_service(
    service_id: int,
    data: ShopServiceIn,
    service: ServiceCatalogService = Depends(get_service_catalog_service),
):
    return await service.update_service(service_id=service_id, data=data)
