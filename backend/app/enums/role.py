from enum import Enum


class UserRoleEnum(str, Enum):
    # Всё, включая наценки
    admin = "admin"
    # Каталог, остатки, сопоставление
    manager = "manager"
