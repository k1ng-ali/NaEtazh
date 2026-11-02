from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class DashboardDay(BaseModel):
    date: date
    # Оформлено в этот день
    orders: int
    # Доставлено в этот день
    revenue: Decimal


class DashboardBuilding(BaseModel):
    # Пусто: адрес не из подключённых домов
    name: str
    orders: int
    revenue: Decimal


class DashboardCourier(BaseModel):
    name: str
    delivered: int
    # Наличные, полученные сегодня: столько курьер должен сдать
    cash: Decimal


class DashboardOut(BaseModel):
    date_from: date
    date_to: date
    orders: int
    delivered: int
    canceled: int
    # Требуют действия менеджера прямо сейчас
    waiting: int
    # Выручка и прибыль только по доставленным заказам
    revenue: Decimal
    profit: Decimal
    profit_complete: bool
    avg_check: Decimal
    days: list[DashboardDay]
    buildings: list[DashboardBuilding]
    couriers_today: list[DashboardCourier]
