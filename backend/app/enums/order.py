from enum import Enum


class OrderStatusEnum(str, Enum):
    new = "new"
    checking = "checking"
    confirmed = "confirmed"
    in_delivery = "in_delivery"
    delivered = "delivered"
    canceled = "canceled"


class AllocationSourceEnum(str, Enum):
    warehouse = "warehouse"
    supplier = "supplier"


class OrderServiceTypeEnum(str, Enum):
    delivery = "delivery"
    lifting = "lifting"
