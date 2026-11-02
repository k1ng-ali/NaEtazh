from datetime import datetime, timezone
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums.order import AllocationSourceEnum, DeliverySlotEnum, OrderEventActionEnum, OrderStatusEnum
from app.enums.role import UserRoleEnum
from app.models.order import Order, OrderEvent
from app.repositories.location_repo import LocationRepository
from app.repositories.order_repo import OrderRepository
from app.repositories.user_repo import UserRepository
from app.schemas.admin_order import (
    AllocationOut,
    CourierOut,
    OrderDeliveryIn,
    OrderEventOut,
    OrderLineAdmin,
    OrderListOutAdmin,
    OrderOutAdmin,
    OrderRowAdmin,
    ServiceLineAdmin,
)
from app.services.checkout_service import format_address

ZERO = Decimal("0")

S = OrderStatusEnum
# Заказ движется только вперёд, отменить можно до доставки
TRANSITIONS: dict[OrderStatusEnum, list[OrderStatusEnum]] = {
    S.new: [S.checking, S.confirmed, S.canceled],
    S.checking: [S.confirmed, S.canceled],
    S.confirmed: [S.in_delivery, S.canceled],
    S.in_delivery: [S.delivered, S.canceled],
    S.delivered: [],
    S.canceled: [],
}
FINAL_STATUSES = (S.delivered, S.canceled)

SLOT_LABELS = {
    DeliverySlotEnum.morning.value: "утро",
    DeliverySlotEnum.day.value: "день",
    DeliverySlotEnum.evening.value: "вечер",
}


class AdminOrderService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = OrderRepository(db=db)
        self.locations = LocationRepository(db=db)
        self.users = UserRepository(db=db)

    # ─── Чтение ───────────────────────────────────────────────────────────────

    async def list_orders(
        self,
        status: str | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> OrderListOutAdmin:
        rows, total = await self.repo.get_orders(status=status, search=search, skip=skip, limit=limit)
        buildings = await self.locations.get_buildings_with_complexes(
            list({order.building_id for order, _ in rows if order.building_id})
        )
        couriers = await self.users.get_names(
            list({order.courier_id for order, _ in rows if order.courier_id})
        )
        items = [
            OrderRowAdmin(
                id=order.id,
                status=order.status,
                created_at=order.created_at,
                customer_name=order.customer_name,
                customer_phone=order.customer_phone,
                address=format_address(order, *buildings.get(order.building_id, (None, None))),
                delivery_date=order.delivery_date,
                delivery_slot=order.delivery_slot,
                planned_date=order.planned_date,
                planned_slot=order.planned_slot,
                courier_name=couriers.get(order.courier_id),
                total=order.total,
                has_supplier_items=has_supplier,
            )
            for order, has_supplier in rows
        ]
        return OrderListOutAdmin(items=items, total=total)

    async def get_order(self, order_id: int) -> OrderOutAdmin:
        order = await self.repo.get_order(order_id)
        if order is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        return await self._order_out(order)

    async def list_couriers(self) -> list[CourierOut]:
        return [CourierOut(id=user.id, name=user.name) for user in await self.users.get_active_couriers()]

    # ─── Действия ─────────────────────────────────────────────────────────────

    async def change_status(self, order_id: int, new_status: OrderStatusEnum, user_id: int) -> OrderOutAdmin:
        order = await self._get_order_for_update_or_404(order_id)
        await self.apply_status(order=order, new_status=new_status, user_id=user_id)
        await self.db.commit()
        await self.db.refresh(order)
        return await self._order_out(order)

    async def apply_status(
        self,
        order: Order,
        new_status: OrderStatusEnum,
        user_id: int | None,
        cash_received: Decimal | None = None,
    ) -> None:
        """Переход статуса со складом и историей. Не делает commit, им пользуется и кабинет курьера."""
        if new_status not in TRANSITIONS[OrderStatusEnum(order.status)]:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Status change not allowed")
        if new_status == S.in_delivery and order.courier_id is None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Courier not assigned")

        if new_status in FINAL_STATUSES:
            # Резерв снимаем в обоих случаях, при доставке ещё и списываем со склада
            for allocation, stock in await self.repo.get_warehouse_allocations_for_update(order_id=order.id):
                stock.reserved = max(stock.reserved - allocation.quantity, ZERO)
                if new_status == S.delivered:
                    stock.quantity = max(stock.quantity - allocation.quantity, ZERO)
        if new_status == S.delivered:
            order.delivered_at = datetime.now(timezone.utc)
            order.cash_received = cash_received

        order.status = new_status.value
        comment = f"Получено наличными: {cash_received:.0f} ₽" if cash_received is not None else None
        await self.repo.add(
            OrderEvent(
                order_id=order.id,
                user_id=user_id,
                action=OrderEventActionEnum.status.value,
                status=new_status.value,
                comment=comment,
            )
        )

    async def set_delivery(self, order_id: int, data: OrderDeliveryIn, user_id: int) -> OrderOutAdmin:
        order = await self._get_order_for_update_or_404(order_id)
        if OrderStatusEnum(order.status) in FINAL_STATUSES:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Order is closed")

        courier_name = None
        if data.courier_id is not None:
            courier = await self.users.get_by_id(data.courier_id)
            if courier is None or courier.role != UserRoleEnum.courier.value or not courier.is_active:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Courier not found")
            courier_name = courier.name
        # Курьер в пути должен оставаться назначенным
        if data.courier_id is None and order.status == S.in_delivery.value:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Courier not assigned")

        order.courier_id = data.courier_id
        order.planned_date = data.planned_date
        order.planned_slot = data.planned_slot.value if data.planned_slot else None

        parts = [f"Курьер: {courier_name}" if courier_name else "Курьер не назначен"]
        if data.planned_date:
            when = f"{data.planned_date:%d.%m}"
            if order.planned_slot:
                when += f", {SLOT_LABELS[order.planned_slot]}"
            parts.append(when)
        await self.repo.add(
            OrderEvent(
                order_id=order.id,
                user_id=user_id,
                action=OrderEventActionEnum.delivery.value,
                comment=", ".join(parts),
            )
        )
        await self.db.commit()
        await self.db.refresh(order)
        return await self._order_out(order)

    async def set_service_cost(self, order_id: int, service_id: int, cost: Decimal | None) -> OrderOutAdmin:
        service = await self.repo.get_service(service_id)
        if service is None or service.order_id != order_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
        service.cost = cost
        await self.db.commit()
        return await self.get_order(order_id)

    async def add_problem(self, order: Order, user_id: int, comment: str) -> None:
        """Проблема в доставке попадает в историю заказа. Не делает commit."""
        await self.repo.add(
            OrderEvent(
                order_id=order.id,
                user_id=user_id,
                action=OrderEventActionEnum.problem.value,
                comment=comment,
            )
        )

    # ─── Хелперы ──────────────────────────────────────────────────────────────

    async def _get_order_for_update_or_404(self, order_id: int) -> Order:
        order = await self.repo.get_order_for_update(order_id)
        if order is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        return order

    async def _order_out(self, order: Order) -> OrderOutAdmin:
        buildings = await self.locations.get_buildings_with_complexes(
            [order.building_id] if order.building_id else []
        )
        building, complex_ = buildings.get(order.building_id, (None, None))
        lines = await self.repo.get_lines(order_id=order.id)
        services = await self.repo.get_services(order_id=order.id)
        allocations = await self.repo.get_allocations(line_ids=[line.id for line in lines])
        events = await self.repo.get_events(order_id=order.id)
        couriers = await self.users.get_names([order.courier_id] if order.courier_id else [])

        by_line: dict[int, list[AllocationOut]] = {}
        goods_cost, complete = ZERO, True
        for allocation, warehouse_name, supplier_name, offer_url in allocations:
            is_warehouse = allocation.source_type == AllocationSourceEnum.warehouse.value
            by_line.setdefault(allocation.order_line_id, []).append(
                AllocationOut(
                    source_type=allocation.source_type,
                    source_name=(warehouse_name if is_warehouse else supplier_name) or "Источник удалён",
                    source_url=None if is_warehouse else offer_url,
                    quantity=allocation.quantity,
                    unit_cost=allocation.unit_cost,
                )
            )
            if allocation.unit_cost is None:
                complete = False
            else:
                goods_cost += allocation.unit_cost * allocation.quantity

        services_cost = ZERO
        for service in services:
            if service.cost is None:
                complete = False
            else:
                services_cost += service.cost
        goods_cost = goods_cost.quantize(Decimal("0.01"))

        return OrderOutAdmin(
            id=order.id,
            public_token=order.public_token,
            status=order.status,
            next_statuses=TRANSITIONS[OrderStatusEnum(order.status)],
            created_at=order.created_at,
            updated_at=order.updated_at,
            customer_name=order.customer_name,
            customer_phone=order.customer_phone,
            contact_channel=order.contact_channel,
            missing_item_policy=order.missing_item_policy,
            address=format_address(order, building, complex_),
            entrance=order.entrance,
            floor=order.floor,
            apartment=order.apartment,
            lifting_type=order.lifting_type,
            delivery_date=order.delivery_date,
            delivery_slot=order.delivery_slot,
            planned_date=order.planned_date,
            planned_slot=order.planned_slot,
            courier_id=order.courier_id,
            courier_name=couriers.get(order.courier_id),
            cash_received=order.cash_received,
            delivered_at=order.delivered_at,
            comment=order.comment,
            source_code=order.source_code,
            lines=[
                OrderLineAdmin(
                    id=line.id,
                    product_id=line.product_id,
                    name=line.name,
                    unit=line.unit,
                    quantity=line.quantity,
                    unit_price=line.unit_price,
                    total=line.total,
                    allocations=by_line.get(line.id, []),
                )
                for line in lines
            ],
            services=[ServiceLineAdmin.model_validate(service, from_attributes=True) for service in services],
            goods_total=order.goods_total,
            services_total=order.services_total,
            total=order.total,
            events=[
                OrderEventOut(
                    action=event.action,
                    status=event.status,
                    comment=event.comment,
                    user_name=user_name,
                    created_at=event.created_at,
                )
                for event, user_name in events
            ],
            goods_cost=goods_cost,
            services_cost=services_cost,
            profit=order.total - goods_cost - services_cost,
            profit_complete=complete,
        )
