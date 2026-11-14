from enum import Enum


class ServiceRequestStatusEnum(str, Enum):
    new = "new"
    # Менеджер связался, договариваются о цене и дате
    in_progress = "in_progress"
    done = "done"
    canceled = "canceled"
