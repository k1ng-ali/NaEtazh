"""
Демо-каталог из предложений партнёра: 100 ходовых товаров для ремонта с фото.

Фото копируются к себе (сжатие в WebP, как при загрузке из админки). Только для демо:
публиковать фото партнёра на боевом сайте можно после его письменного разрешения.
Повторный запуск добирает товары до квоты и не создаёт дублей.

Запуск: python -m scripts.seed_partner_demo
"""

import asyncio
import sys

import httpx
from sqlalchemy import func, select
from starlette.concurrency import run_in_threadpool

from app.core.database import AsyncSessionLocal
from app.core.media import InvalidImageError, compress_image, save_media
from app.enums.product_status import ProductStatusEnum
from app.models import Category, Product, Supplier, SupplierOffer
from app.services.supplier_service import SupplierService

SUPPLIER_CODE = "famarket"
# Партнёр не должен заметить нагрузку
DOWNLOAD_PAUSE_S = 0.3

# Наш раздел (название, slug, slug родителя) → квота и категории партнёра
SECTIONS = [
    ("Штукатурка", "shtukaturka", None, 12, [
        "Грунтовка для штукатурки стен", "Бетон-контакт", "Для потолков и стен",
        "Маячковые профили и штукатурные уголки", "Правило штукатурное",
    ]),
    ("Шпаклёвка", "shpaklevka", None, 10, [
        "Сухая шпаклевка в мешках", "Готовые финишные шпаклевки", "Серпянка", "Стеклохолст, стеклообои",
    ]),
    ("Гипсокартон", "gipsokarton", None, 10, [
        "Гипсокартон", "Гипсокартон влагостойкий (ГКЛВ)", "Гипсовые пазогребневые плиты (ПГП)",
        "Саморезы по ГКЛ",
    ]),
    ("Профиль", "profil", None, 8, ["Профиль для гипсокартона", "Подвесы и соединители для профиля"]),
    ("Шумоизоляция", "shumoizolyatsiya", None, 6, [
        "Базальтовая звукоизоляция", "Рулонная шумоизоляция", "Комплектующие для шумоизоляции",
        "Минеральная звукоизоляция",
    ]),
    ("Пол", "pol", None, 10, [
        "Наливной пол", "Армированная стяжка пола", "Пескобетон М300", "Подложка под ламинат",
    ]),
    ("Плитка: клей и затирка", "plitka", None, 10, [
        "Клей для плитки и камня", "Влагостойкий клей для плитки", "Затирки для швов плитки",
        "Гидроизоляционные смеси", "Гидроизоляционная лента",
    ]),
    ("Краски и малярный инструмент", "kraski", None, 12, [
        "Краски и эмали Злата", "Краски и эмали Мастер-Класс", "Краски и эмали Текс",
        "Краски и эмали Фарбокс", "Малярные валики и шубки", "Малярные кисти и краскопульты",
        "Малярные удочки, ручки и ванночки для валиков", "Лента и скотч", "Клей для обоев",
    ]),
    ("Электрика", "elektrika", None, 10, [
        "Автоматические выключатели", "Электроустановочные элементы",
        "Кабель силовой ВВГнг LS медный", "Гофры и комплектующие",
    ]),
    ("Освещения", "osvescheniya", "elektrika", 4, ["Освещение"]),
    ("Пена, герметики, крепёж", "montazh", None, 8, [
        "Пена монтажная", "Герметики и жидкие гвозди", "Жидкие гвозди", "Дюбель-гвозди",
        "Дюбель пластиковый",
    ]),
]


async def get_or_create_category(db, name: str, slug: str, parent_slug: str | None) -> Category:
    category = await db.scalar(select(Category).where(Category.slug == slug))
    if category is not None:
        return category
    parent_id = None
    if parent_slug:
        parent_id = (await get_or_create_category(db, parent_slug, parent_slug, None)).id
    position = await db.scalar(select(func.count(Category.id)))
    category = Category(name=name, slug=slug, parent_id=parent_id, position=position)
    db.add(category)
    await db.commit()
    return category


async def candidates(db, supplier_id: int, partner_categories: list[str]) -> list[SupplierOffer]:
    """Свободные предложения в наличии с фото, по очереди из каждой категории партнёра."""
    result = await db.scalars(
        select(SupplierOffer)
        .where(
            SupplierOffer.supplier_id == supplier_id,
            SupplierOffer.is_active.is_(True),
            SupplierOffer.product_id.is_(None),
            SupplierOffer.quantity > 0,
            SupplierOffer.picture_url.is_not(None),
            SupplierOffer.category_name.in_(partner_categories),
        )
        .order_by(SupplierOffer.quantity.desc(), SupplierOffer.id)
    )
    by_category: dict[str, list[SupplierOffer]] = {name: [] for name in partner_categories}
    for offer in result:
        by_category[offer.category_name].append(offer)
    # Чередуем категории, чтобы раздел не состоял из одних грунтовок
    ordered = []
    while any(by_category.values()):
        for queue in by_category.values():
            if queue:
                ordered.append(queue.pop(0))
    return ordered


async def download_photo(client: httpx.AsyncClient, url: str) -> str | None:
    try:
        response = await client.get(url)
        response.raise_for_status()
        compressed = await run_in_threadpool(compress_image, response.content)
    except (httpx.HTTPError, InvalidImageError) as exc:
        print(f"  фото не скачалось: {url} ({type(exc).__name__})", file=sys.stderr)
        return None
    return await run_in_threadpool(save_media, compressed, "products")


async def main() -> int:
    created_total = 0
    async with AsyncSessionLocal() as db, httpx.AsyncClient(
        timeout=20, follow_redirects=True, headers={"User-Agent": "StroyBaza97 demo import"}
    ) as client:
        supplier = await db.scalar(select(Supplier).where(Supplier.code == SUPPLIER_CODE))
        if supplier is None:
            print("Поставщик famarket не найден: сначала импортируйте выгрузку", file=sys.stderr)
            return 1
        service = SupplierService(db=db)

        for name, slug, parent_slug, quota, partner_categories in SECTIONS:
            category = await get_or_create_category(db, name, slug, parent_slug)
            # Товары партнёра в разделе уже есть: добираем только недостающие
            linked = await db.scalar(
                select(func.count(Product.id))
                .join(SupplierOffer, SupplierOffer.product_id == Product.id)
                .where(Product.category_id == category.id, SupplierOffer.supplier_id == supplier.id)
            )
            need = quota - linked
            created = 0
            for offer in await candidates(db, supplier.id, partner_categories):
                if created >= need:
                    break
                image = await download_photo(client, offer.picture_url)
                await asyncio.sleep(DOWNLOAD_PAUSE_S)
                if image is None:
                    continue
                out = await service.create_product_from_offer(offer_id=offer.id, category_id=category.id)
                product = await db.get(Product, out.product_id)
                product.images = [image]
                product.status = ProductStatusEnum.published.value
                await db.commit()
                created += 1
            created_total += created
            print(f"{name}: +{created}, всего {linked + created} из {quota}")

        # Товары, связанные с партнёром раньше вручную, остались без фото
        without_photo = await db.execute(
            select(Product, SupplierOffer.picture_url)
            .join(SupplierOffer, SupplierOffer.product_id == Product.id)
            .where(
                SupplierOffer.supplier_id == supplier.id,
                SupplierOffer.picture_url.is_not(None),
                func.jsonb_array_length(Product.images) == 0,
            )
        )
        filled = 0
        for product, picture_url in without_photo.all():
            image = await download_photo(client, picture_url)
            await asyncio.sleep(DOWNLOAD_PAUSE_S)
            if image is not None:
                product.images = [image]
                filled += 1
        await db.commit()

    print(f"Создано товаров: {created_total}, добавлено фото к старым: {filled}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
