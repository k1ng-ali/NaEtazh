from fastapi import APIRouter, Depends, Query

from app.deps.auth import require_admin
from app.deps.services import get_dashboard_service
from app.schemas.dashboard import DashboardOut
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Admin • Dashboard"], dependencies=[Depends(require_admin)])


@router.get("/", response_model=DashboardOut)
async def get_dashboard(
    days: int = Query(7, ge=1, le=90),
    service: DashboardService = Depends(get_dashboard_service),
):
    return await service.get_dashboard(days=days)
