from fastapi import APIRouter, Depends

from app.deps.auth import require_admin
from app.deps.services import get_admin_order_service
from app.schemas.admin_order import OrderOutAdmin, ServiceCostIn
from app.services.admin_order_service import AdminOrderService

# Деньги заказа видит только владелец, работа с заказом — в домене менеджера
router = APIRouter(prefix="/orders", tags=["Admin • Orders"], dependencies=[Depends(require_admin)])


@router.get("/{order_id}", response_model=OrderOutAdmin)
async def get_order(order_id: int, service: AdminOrderService = Depends(get_admin_order_service)):
    return await service.get_order(order_id=order_id)


@router.put("/{order_id}/services/{service_id}/cost", response_model=OrderOutAdmin)
async def set_service_cost(
    order_id: int,
    service_id: int,
    data: ServiceCostIn,
    service: AdminOrderService = Depends(get_admin_order_service),
):
    return await service.set_service_cost(order_id=order_id, service_id=service_id, cost=data.cost)
