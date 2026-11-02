from enum import Enum


class AvailabilityEnum(str, Enum):
    # Есть на своём складе
    in_stock = "in_stock"
    # Привезём от партнёра
    on_order = "on_order"
    unavailable = "unavailable"
