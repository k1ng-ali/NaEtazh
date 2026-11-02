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


class LiftingTypeEnum(str, Enum):
    # Покупатель поднимает сам
    none = "none"
    lift = "lift"
    stairs = "stairs"


class DeliverySlotEnum(str, Enum):
    morning = "morning"
    day = "day"
    evening = "evening"


class ContactChannelEnum(str, Enum):
    call = "call"
    whatsapp = "whatsapp"
    telegram = "telegram"


class MissingItemPolicyEnum(str, Enum):
    # Позвонить и решить вместе
    call = "call"
    # Заменить аналогом той же цены или дешевле
    replace = "replace"
    # Привезти остальное без этого товара
    skip = "skip"


class OrderEventActionEnum(str, Enum):
    created = "created"
    status = "status"
    # Назначен курьер или согласована дата
    delivery = "delivery"
    # Курьер сообщил о проблеме
    problem = "problem"
