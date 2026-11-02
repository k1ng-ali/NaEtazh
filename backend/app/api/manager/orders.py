from fastapi import APIRouter, Depends, Query

from app.deps.auth import require_staff
from app.deps.services import get_admin_order_service
from app.enums.order import OrderStatusEnum
from app.schemas.admin_order import (
    CourierOut,
    OrderDeliveryIn,
    OrderListOutAdmin,
    OrderOutManager,
    OrderStatusIn,
)
from app.schemas.auth import CurrentUser
from app.services.admin_order_service import AdminOrderService

# Ответы без расходов и прибыли: лишние поля отрезает response_model
router = APIRouter(tags=["Manager • Orders"])


@router.get("/orders/", response_model=OrderListOutAdmin, dependencies=[Depends(require_staff)])
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


@router.get("/orders/{order_id}", response_model=OrderOutManager, dependencies=[Depends(require_staff)])
async def get_order(order_id: int, service: AdminOrderService = Depends(get_admin_order_service)):
    return await service.get_order(order_id=order_id)


@router.post("/orders/{order_id}/status", response_model=OrderOutManager)
async def change_status(
    order_id: int,
    data: OrderStatusIn,
    user: CurrentUser = Depends(require_staff),
    service: AdminOrderService = Depends(get_admin_order_service),
):
    return await service.change_status(order_id=order_id, new_status=data.status, user_id=user.id)


@router.put("/orders/{order_id}/delivery", response_model=OrderOutManager)
async def set_delivery(
    order_id: int,
    data: OrderDeliveryIn,
    user: CurrentUser = Depends(require_staff),
    service: AdminOrderService = Depends(get_admin_order_service),
):
    return await service.set_delivery(order_id=order_id, data=data, user_id=user.id)


@router.get("/couriers/", response_model=list[CourierOut], dependencies=[Depends(require_staff)])
async def list_couriers(service: AdminOrderService = Depends(get_admin_order_service)):
    return await service.list_couriers()
