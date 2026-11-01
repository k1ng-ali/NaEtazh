from enum import Enum


class ProductStatusEnum(str, Enum):
    draft = "draft"
    published = "published"
    archived = "archived"
