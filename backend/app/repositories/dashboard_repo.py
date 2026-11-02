from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, case, cast, func, select

from app.enums.order import OrderStatusEnum
from app.models.location import Building, ResidentialComplex
from app.models.order import Order, OrderAllocation, OrderLine, OrderServiceLine
from app.models.user import User
from app.repositories.base_repo import BaseRepository

ZERO = Decimal("0")


class DashboardRepository(BaseRepository):

    @staticmethod
    def _local_date(column, timezone: str):
        # День считаем по часовому поясу магазина, а не по UTC
        return cast(func.timezone(timezone, column), Date)

    async def get_order_counts(self, since: datetime, until: datetime) -> dict[str, int]:
        result = await self.db.execute(
            select(Order.status, func.count(Order.id))
            .where(Order.created_at >= since, Order.created_at < until)
            .group_by(Order.status)
        )
        return {status: count for status, count in result.all()}

    async def count_waiting(self) -> int:
        result = await self.db.execute(
            select(func.count(Order.id)).where(
                Order.status.in_([OrderStatusEnum.new.value, OrderStatusEnum.checking.value])
            )
        )
        return result.scalar() or 0

    async def get_delivered_money(
        self, since: datetime, until: datetime
    ) -> tuple[Decimal, Decimal, int, bool]:
        """Выручка, себестоимость, число доставленных и полнота себестоимости."""
        delivered = (
            select(Order.id, Order.total)
            .where(
                Order.status == OrderStatusEnum.delivered.value,
                Order.delivered_at >= since,
                Order.delivered_at < until,
            )
            .subquery()
        )
        revenue = await self.db.execute(
            select(func.coalesce(func.sum(delivered.c.total), 0), func.count(delivered.c.id))
        )
        revenue_sum, delivered_count = revenue.one()

        goods = await self.db.execute(
            select(
                func.coalesce(func.sum(OrderAllocation.quantity * OrderAllocation.unit_cost), 0),
                func.count(case((OrderAllocation.unit_cost.is_(None), 1))),
            )
            .join(OrderLine, OrderLine.id == OrderAllocation.order_line_id)
            .where(OrderLine.order_id.in_(select(delivered.c.id)))
        )
        goods_cost, goods_missing = goods.one()

        services = await self.db.execute(
            select(
                func.coalesce(func.sum(OrderServiceLine.cost), 0),
                func.count(case((OrderServiceLine.cost.is_(None), 1))),
            ).where(OrderServiceLine.order_id.in_(select(delivered.c.id)))
        )
        services_cost, services_missing = services.one()

        return (
            Decimal(revenue_sum),
            Decimal(goods_cost) + Decimal(services_cost),
            delivered_count,
            goods_missing == 0 and services_missing == 0,
        )

    async def get_orders_by_day(self, since: datetime, until: datetime, timezone: str) -> dict[date, int]:
        day = self._local_date(Order.created_at, timezone)
        result = await self.db.execute(
            select(day, func.count(Order.id))
            .where(Order.created_at >= since, Order.created_at < until)
            .group_by(day)
        )
        return {value: count for value, count in result.all()}

    async def get_revenue_by_day(
        self, since: datetime, until: datetime, timezone: str
    ) -> dict[date, Decimal]:
        day = self._local_date(Order.delivered_at, timezone)
        result = await self.db.execute(
            select(day, func.sum(Order.total))
            .where(
                Order.status == OrderStatusEnum.delivered.value,
                Order.delivered_at >= since,
                Order.delivered_at < until,
            )
            .group_by(day)
        )
        return {value: total for value, total in result.all()}

    async def get_buildings(
        self, since: datetime, until: datetime
    ) -> list[tuple[str | None, str | None, int, Decimal]]:
        """Заказы по корпусам без отменённых: какие визитки работают."""
        result = await self.db.execute(
            select(ResidentialComplex.name, Building.name, func.count(Order.id), func.sum(Order.total))
            .select_from(Order)
            .outerjoin(Building, Building.id == Order.building_id)
            .outerjoin(ResidentialComplex, ResidentialComplex.id == Building.complex_id)
            .where(
                Order.created_at >= since,
                Order.created_at < until,
                Order.status != OrderStatusEnum.canceled.value,
            )
            .group_by(ResidentialComplex.name, Building.name)
            .order_by(func.count(Order.id).desc())
        )
        return [tuple(row) for row in result.all()]

    async def get_couriers_cash(self, since: datetime) -> list[tuple[str, int, Decimal]]:
        result = await self.db.execute(
            select(User.name, func.count(Order.id), func.coalesce(func.sum(Order.cash_received), 0))
            .join(User, User.id == Order.courier_id)
            .where(Order.status == OrderStatusEnum.delivered.value, Order.delivered_at >= since)
            .group_by(User.name)
            .order_by(User.name)
        )
        return [tuple(row) for row in result.all()]
