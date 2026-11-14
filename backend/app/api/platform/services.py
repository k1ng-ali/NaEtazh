from fastapi import APIRouter, BackgroundTasks, Depends, status

from app.core.telegram import send_telegram_message
from app.deps.services import get_service_catalog_service
from app.schemas.service import (
    ServiceRequestCreatedOut,
    ServiceRequestCreateIn,
    ShopContactsOut,
    ShopServiceOut,
)
from app.services.service_catalog_service import ServiceCatalogService

router = APIRouter(tags=["Platform • Services"])


@router.get("/services/", response_model=list[ShopServiceOut])
async def list_services(service: ServiceCatalogService = Depends(get_service_catalog_service)):
    return await service.list_services()


@router.get("/shop/contacts", response_model=ShopContactsOut)
async def get_contacts(service: ServiceCatalogService = Depends(get_service_catalog_service)):
    return await service.get_contacts()


@router.get("/services/{slug}", response_model=ShopServiceOut)
async def get_service(slug: str, service: ServiceCatalogService = Depends(get_service_catalog_service)):
    return await service.get_service(slug=slug)


@router.post(
    "/service-requests/", response_model=ServiceRequestCreatedOut, status_code=status.HTTP_201_CREATED
)
async def create_service_request(
    data: ServiceRequestCreateIn,
    background_tasks: BackgroundTasks,
    service: ServiceCatalogService = Depends(get_service_catalog_service),
):
    created, notification = await service.create_request(data=data)
    # Уведомление уходит после ответа покупателю и не задерживает его
    background_tasks.add_task(send_telegram_message, notification)
    return created
