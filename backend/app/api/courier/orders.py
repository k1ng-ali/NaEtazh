from fastapi import APIRouter, BackgroundTasks, Depends

from app.core.telegram import send_telegram_message
from app.deps.auth import require_courier
from app.deps.services import get_courier_service
from app.schemas.auth import CurrentUser
from app.schemas.courier import CourierDeliverIn, CourierOrderOut, CourierOrderRow, CourierProblemIn
from app.services.courier_service import CourierService

router = APIRouter(prefix="/orders", tags=["Courier • Orders"])


@router.get("/", response_model=list[CourierOrderRow])
async def list_orders(
    user: CurrentUser = Depends(require_courier),
    service: CourierService = Depends(get_courier_service),
):
    return await service.list_orders(courier_id=user.id)


@router.get("/{order_id}", response_model=CourierOrderOut)
async def get_order(
    order_id: int,
    user: CurrentUser = Depends(require_courier),
    service: CourierService = Depends(get_courier_service),
):
    return await service.get_order(courier_id=user.id, order_id=order_id)


@router.post("/{order_id}/start", response_model=CourierOrderOut)
async def start_delivery(
    order_id: int,
    user: CurrentUser = Depends(require_courier),
    service: CourierService = Depends(get_courier_service),
):
    return await service.start(courier_id=user.id, order_id=order_id)


@router.post("/{order_id}/deliver", response_model=CourierOrderOut)
async def deliver(
    order_id: int,
    data: CourierDeliverIn,
    background_tasks: BackgroundTasks,
    user: CurrentUser = Depends(require_courier),
    service: CourierService = Depends(get_courier_service),
):
    order, notification = await service.deliver(
        courier_id=user.id, order_id=order_id, cash_received=data.cash_received
    )
    if notification:
        background_tasks.add_task(send_telegram_message, notification)
    return order


@router.post("/{order_id}/problem", response_model=CourierOrderOut)
async def report_problem(
    order_id: int,
    data: CourierProblemIn,
    background_tasks: BackgroundTasks,
    user: CurrentUser = Depends(require_courier),
    service: CourierService = Depends(get_courier_service),
):
    order, notification = await service.report_problem(
        courier_id=user.id, order_id=order_id, comment=data.comment
    )
    background_tasks.add_task(send_telegram_message, notification)
    return order
