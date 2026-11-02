from enum import Enum


class UserRoleEnum(str, Enum):
    # Владелец: деньги, наценка, тарифы, сотрудники и всё, что видит менеджер
    admin = "admin"
    # Заказы, каталог, остатки, сопоставление с партнёром
    manager = "manager"
    # Только назначенные ему доставки
    courier = "courier"
