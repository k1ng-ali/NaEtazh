"""
Демо-данные для локальной разработки. Цены условные.

Запуск: python -m scripts.seed_demo
"""

import asyncio
from decimal import Decimal

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.enums.product_status import ProductStatusEnum
from app.enums.role import UserRoleEnum
from app.models import Category, PricingRule, Product, User

CATEGORIES = [
    ("Штукатурка", "shtukaturka"),
    ("Гипсокартон", "gipsokarton"),
    ("Профиль", "profil"),
    ("Шумоизоляция", "shumoizolyatsiya"),
]

PRODUCTS = [
    (
        "shtukaturka",
        "DEMO-1",
        "Штукатурка гипсовая Кнауф Ротбанд, 30 кг",
        "rotband-30",
        "мешок",
        "430",
        "30",
        None,
    ),
    ("shtukaturka", "DEMO-2", "Штукатурка Волма Слой, 30 кг", "volma-sloy-30", "мешок", "370", "30", None),
    (
        "gipsokarton",
        "DEMO-3",
        "Гипсокартон Кнауф влагостойкий, 2500×1200×12,5 мм",
        "gklv-125",
        "лист",
        "440",
        "26",
        2500,
    ),
    ("profil", "DEMO-4", "Профиль потолочный ПП, 60×27 мм, 3 м", "profil-pp-3", "шт", "175", "1.5", 3000),
]


# Только для локальной разработки, на сервере сотрудников создаёт scripts.create_user
DEMO_ADMIN_LOGIN = "admin"
DEMO_ADMIN_PASSWORD = "admin-demo-2026"
# Логин, имя и роль; пароль у всех демо-сотрудников один
DEMO_STAFF = [
    (DEMO_ADMIN_LOGIN, "Администратор", UserRoleEnum.admin),
    ("manager", "Менеджер Анна", UserRoleEnum.manager),
    ("courier", "Курьер Сергей", UserRoleEnum.courier),
]


async def seed_staff(db) -> None:
    for login, name, role in DEMO_STAFF:
        existing = await db.execute(select(User.id).where(User.login == login))
        if existing.scalar() is not None:
            continue
        db.add(
            User(login=login, password_hash=hash_password(DEMO_ADMIN_PASSWORD), name=name, role=role.value)
        )
        print(f"Демо-сотрудник: {login} ({role.value})")
    # Условная наценка, чтобы импорт партнёра сразу считал цены
    if (await db.execute(select(PricingRule.id).limit(1))).scalar() is None:
        db.add(PricingRule(category_id=None, markup_percent=Decimal("20"), min_profit=Decimal("30")))
    await db.commit()


async def main() -> None:
    async with AsyncSessionLocal() as db:
        await seed_staff(db)

        existing = await db.execute(select(Category.id).limit(1))
        if existing.scalar() is not None:
            print("Каталог уже заполнен, пропускаем")
            return

        categories = {}
        for position, (name, slug) in enumerate(CATEGORIES):
            category = Category(name=name, slug=slug, position=position)
            db.add(category)
            categories[slug] = category
        await db.flush()

        for category_slug, sku, name, slug, unit, price, weight, length in PRODUCTS:
            db.add(
                Product(
                    category_id=categories[category_slug].id,
                    sku=sku,
                    name=name,
                    slug=slug,
                    unit=unit,
                    price=Decimal(price),
                    weight_kg=Decimal(weight),
                    length_mm=length,
                    images=[],
                    attributes={},
                    status=ProductStatusEnum.published.value,
                )
            )
        await db.commit()
        print("Демо-данные добавлены")


if __name__ == "__main__":
    asyncio.run(main())
