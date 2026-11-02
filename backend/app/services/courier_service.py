from datetime import date, datetime, time
from decimal import Decimal
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.enums.order import DeliverySlotEnum, OrderStatusEnum
from app.models.order import Order
from app.repositories.location_repo import LocationRepository
from app.repositories.order_repo import OrderRepository
from app.repositories.user_repo import UserRepository
from app.schemas.courier import CourierLineOut, CourierOrderOut, CourierOrderRow
from app.services.admin_order_service import AdminOrderService
from app.services.checkout_service import format_address

SLOT_ORDER = {
    DeliverySlotEnum.morning.value: 0,
    DeliverySlotEnum.day.value: 1,
    DeliverySlotEnum.evening.value: 2,
}


def today_start() -> datetime:
    """Начало сегодняшнего дня в часовом поясе магазина."""
    zone = ZoneInfo(settings.TIMEZONE)
    return datetime.combine(datetime.now(zone).date(), time.min, tzinfo=zone)


class CourierService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = OrderRepository(db=db)
        self.locations = LocationRepository(db=db)
        self.users = UserRepository(db=db)
        self.workflow = AdminOrderService(db=db)

    async def list_orders(self, courier_id: int) -> list[CourierOrderRow]:
        orders = await self.repo.get_courier_orders(courier_id=courier_id, delivered_since=today_start())
        buildings = await self.locations.get_buildings_with_complexes(
            list({order.building_id for order in orders if order.building_id})
        )
        # Сначала то, что везти, по дате и времени; отвезённое сегодня в конце
        orders.sort(
            key=lambda order: (
                order.status == OrderStatusEnum.delivered.value,
                order.planned_date or date.max,
                SLOT_ORDER.get(order.planned_slot, 3),
                order.id,
            )
        )
        return [
            CourierOrderRow(
                id=order.id,
                status=order.status,
                planned_date=order.planned_date,
                planned_slot=order.planned_slot,
                address=format_address(order, *buildings.get(order.building_id, (None, None))),
                lifting_type=order.lifting_type,
                total=order.total,
            )
            for order in orders
        ]

    async def get_order(self, courier_id: int, order_id: int) -> CourierOrderOut:
        order = await self.repo.get_order(order_id)
        return await self._order_out(self._check_owner(order, courier_id))

    async def start(self, courier_id: int, order_id: int) -> CourierOrderOut:
        order = self._check_owner(await self.repo.get_order_for_update(order_id), courier_id)
        await self.workflow.apply_status(
            order=order, new_status=OrderStatusEnum.in_delivery, user_id=courier_id
        )
        return await self._commit_and_out(order)

    async def deliver(
        self, courier_id: int, order_id: int, cash_received: Decimal
    ) -> tuple[CourierOrderOut, str | None]:
        """Заказ отвезён. Второе значение — сообщение менеджеру, если сумма не сошлась."""
        order = self._check_owner(await self.repo.get_order_for_update(order_id), courier_id)
        await self.workflow.apply_status(
            order=order,
            new_status=OrderStatusEnum.delivered,
            user_id=courier_id,
            cash_received=cash_received,
        )
        result = await self._commit_and_out(order)
        if cash_received == order.total:
            return result, None
        courier_name = (await self.users.get_names([courier_id])).get(courier_id, "Курьер")
        return result, (
            f"Заказ № {order.id} доставлен, но сумма не сошлась\n"
            f"{courier_name} получил {cash_received:.0f} ₽ вместо {order.total:.0f} ₽"
        )

    async def report_problem(
        self, courier_id: int, order_id: int, comment: str
    ) -> tuple[CourierOrderOut, str]:
        order = self._check_owner(await self.repo.get_order_for_update(order_id), courier_id)
        await self.workflow.add_problem(order=order, user_id=courier_id, comment=comment.strip())
        result = await self._commit_and_out(order)
        courier_name = (await self.users.get_names([courier_id])).get(courier_id, "Курьер")
        return result, f"Проблема с заказом № {order.id}\n{courier_name}: {comment.strip()}\n{result.address}"

    # ─── Хелперы ──────────────────────────────────────────────────────────────

    @staticmethod
    def _check_owner(order: Order | None, courier_id: int) -> Order:
        # Чужой заказ для курьера не существует: не подсказываем, что такой номер есть
        if order is None or order.courier_id != courier_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        return order

    async def _commit_and_out(self, order: Order) -> CourierOrderOut:
        await self.db.commit()
        await self.db.refresh(order)
        return await self._order_out(order)

    async def _order_out(self, order: Order) -> CourierOrderOut:
        buildings = await self.locations.get_buildings_with_complexes(
            [order.building_id] if order.building_id else []
        )
        building, complex_ = buildings.get(order.building_id, (None, None))
        if complex_ is not None:
            map_address = complex_.address or complex_.name
        else:
            map_address = order.address_text or ""
        lines = await self.repo.get_lines(order_id=order.id)
        return CourierOrderOut(
            id=order.id,
            status=order.status,
            planned_date=order.planned_date,
            planned_slot=order.planned_slot,
            address=format_address(order, building, complex_),
            map_address=map_address,
            entrance=order.entrance,
            floor=order.floor,
            apartment=order.apartment,
            lifting_type=order.lifting_type,
            customer_name=order.customer_name,
            customer_phone=order.customer_phone,
            contact_channel=order.contact_channel,
            comment=order.comment,
            lines=[CourierLineOut(name=line.name, unit=line.unit, quantity=line.quantity) for line in lines],
            total=order.total,
            cash_received=order.cash_received,
            delivered_at=order.delivered_at,
        )
