from fastapi import APIRouter, BackgroundTasks, Depends, status

from app.core.telegram import send_telegram_message
from app.deps.services import get_checkout_service
from app.schemas.checkout import (
    OrderCreatedOut,
    OrderCreateIn,
    OrderPublicOut,
    QuoteIn,
    QuoteOut,
)
from app.schemas.location import BuildingPublicOut
from app.services.checkout_service import CheckoutService

router = APIRouter(tags=["Platform • Checkout"])


@router.get("/buildings/{code}", response_model=BuildingPublicOut)
async def get_building(code: str, service: CheckoutService = Depends(get_checkout_service)):
    return await service.get_building(code=code)


@router.post("/cart/quote", response_model=QuoteOut)
async def quote_cart(data: QuoteIn, service: CheckoutService = Depends(get_checkout_service)):
    return await service.quote(data=data)


@router.post("/orders/", response_model=OrderCreatedOut, status_code=status.HTTP_201_CREATED)
async def create_order(
    data: OrderCreateIn,
    background_tasks: BackgroundTasks,
    service: CheckoutService = Depends(get_checkout_service),
):
    created, notification = await service.create_order(data=data)
    # Уведомление уходит после ответа покупателю и не задерживает его
    background_tasks.add_task(send_telegram_message, notification)
    return created


@router.get("/orders/{token}", response_model=OrderPublicOut)
async def get_order(token: str, service: CheckoutService = Depends(get_checkout_service)):
    return await service.get_public_order(token=token)
