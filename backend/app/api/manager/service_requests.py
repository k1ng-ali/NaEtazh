from fastapi import APIRouter, Depends, Query

from app.deps.auth import require_staff
from app.deps.services import get_service_catalog_service
from app.enums.service_request import ServiceRequestStatusEnum
from app.schemas.service import ServiceRequestListOut, ServiceRequestOut, ServiceRequestStatusIn
from app.services.service_catalog_service import ServiceCatalogService

router = APIRouter(
    prefix="/service-requests",
    tags=["Manager • Service requests"],
    dependencies=[Depends(require_staff)],
)


@router.get("/", response_model=ServiceRequestListOut)
async def list_requests(
    status: ServiceRequestStatusEnum | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    service: ServiceCatalogService = Depends(get_service_catalog_service),
):
    return await service.list_requests(status=status.value if status else None, skip=skip, limit=limit)


@router.patch("/{request_id}", response_model=ServiceRequestOut)
async def set_request_status(
    request_id: int,
    data: ServiceRequestStatusIn,
    service: ServiceCatalogService = Depends(get_service_catalog_service),
):
    return await service.set_request_status(request_id=request_id, new_status=data.status.value)
