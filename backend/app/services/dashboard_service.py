from datetime import datetime, time, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.enums.order import OrderStatusEnum
from app.repositories.dashboard_repo import DashboardRepository
from app.schemas.dashboard import DashboardBuilding, DashboardCourier, DashboardDay, DashboardOut
from app.services.courier_service import today_start

CENT = Decimal("0.01")


class DashboardService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = DashboardRepository(db=db)

    async def get_dashboard(self, days: int) -> DashboardOut:
        """Сводка за последние days дней, включая сегодня."""
        zone = ZoneInfo(settings.TIMEZONE)
        today = datetime.now(zone).date()
        date_from = today - timedelta(days=days - 1)
        since = datetime.combine(date_from, time.min, tzinfo=zone)
        until = datetime.combine(today + timedelta(days=1), time.min, tzinfo=zone)

        counts = await self.repo.get_order_counts(since=since, until=until)
        revenue, cost, delivered, complete = await self.repo.get_delivered_money(since=since, until=until)
        orders_by_day = await self.repo.get_orders_by_day(
            since=since, until=until, timezone=settings.TIMEZONE
        )
        revenue_by_day = await self.repo.get_revenue_by_day(
            since=since, until=until, timezone=settings.TIMEZONE
        )

        return DashboardOut(
            date_from=date_from,
            date_to=today,
            orders=sum(counts.values()),
            delivered=delivered,
            canceled=counts.get(OrderStatusEnum.canceled.value, 0),
            waiting=await self.repo.count_waiting(),
            revenue=revenue,
            profit=(revenue - cost).quantize(CENT),
            profit_complete=complete,
            avg_check=(revenue / delivered).quantize(CENT) if delivered else Decimal("0"),
            days=[
                DashboardDay(
                    date=day,
                    orders=orders_by_day.get(day, 0),
                    revenue=revenue_by_day.get(day, Decimal("0")),
                )
                for day in (date_from + timedelta(days=offset) for offset in range(days))
            ],
            buildings=[
                DashboardBuilding(
                    name=f"{complex_name}, {building_name}" if complex_name else "Другие адреса",
                    orders=orders,
                    delivered=delivered_count,
                    canceled=canceled_count,
                    revenue=total,
                )
                for (
                    complex_name,
                    building_name,
                    orders,
                    delivered_count,
                    canceled_count,
                    total,
                ) in await self.repo.get_buildings(since=since, until=until)
            ],
            couriers_today=[
                DashboardCourier(name=name, delivered=count, cash=cash)
                for name, count, cash in await self.repo.get_couriers_cash(since=today_start())
            ],
        )
