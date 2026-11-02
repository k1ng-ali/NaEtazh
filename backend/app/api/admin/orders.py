from fastapi import APIRouter, Depends, Query

from app.deps.auth import require_staff
from app.deps.services import get_admin_order_service
from app.enums.order import OrderStatusEnum
from app.schemas.admin_order import OrderListOutAdmin, OrderOutAdmin, OrderStatusIn, ServiceCostIn
from app.services.admin_order_service import AdminOrderService

router = APIRouter(prefix="/orders", tags=["Admin • Orders"], dependencies=[Depends(require_staff)])


@router.get("/", response_model=OrderListOutAdmin)
async def list_orders(
    status: OrderStatusEnum | None = None,
    search: str | None = Query(None, max_length=100),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    service: AdminOrderService = Depends(get_admin_order_service),
):
    return await service.list_orders(
        status=status.value if status else None,
        search=search,
        skip=skip,
        limit=limit,
    )


@router.get("/{order_id}", response_model=OrderOutAdmin)
async def get_order(order_id: int, service: AdminOrderService = Depends(get_admin_order_service)):
    return await service.get_order(order_id=order_id)


@router.post("/{order_id}/status", response_model=OrderOutAdmin)
async def change_status(
    order_id: int,
    data: OrderStatusIn,
    service: AdminOrderService = Depends(get_admin_order_service),
):
    return await service.change_status(order_id=order_id, new_status=data.status)


@router.put("/{order_id}/services/{service_id}/cost", response_model=OrderOutAdmin)
async def set_service_cost(
    order_id: int,
    service_id: int,
    data: ServiceCostIn,
    service: AdminOrderService = Depends(get_admin_order_service),
):
    return await service.set_service_cost(order_id=order_id, service_id=service_id, cost=data.cost)
