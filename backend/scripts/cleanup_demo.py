"""
Убирает демо-данные: 100 товаров демо-каталога, демо-товары DEMO-*, тестовые товары и
демо-разделы.

Что считается демо:
- товары партнёра, заведённые раньше первого импорта дерева разделов партнёра: до него
  товары партнёра заводил только демо-скрипт, потом их заводит сам импорт;
- товары с артикулом DEMO-* (scripts.seed_demo);
- любые товары в демо-разделах: 11 разделов демо-каталога и скрытые old-*.
Свои товары, заведённые вручную в обычных разделах, не трогаются.

Товар, который есть в заказах, удалить нельзя: он уходит в архив и отвязывается от
партнёра, чтобы импорт завёл вместо него новый товар. Остальные удаляются вместе со своими
фото. Пустые демо-разделы удаляются. Если товары партнёра включены на витрине, импорт сразу
заводит товары заново, уже в разделах как у партнёра; фото — по ссылке партнёра, свои
копии докачает cron.

Запуск: python -m scripts.cleanup_demo            — только показать, что будет сделано
        python -m scripts.cleanup_demo --apply    — сделать
"""

import argparse
import asyncio
import sys

from sqlalchemy import func, or_, select

from app.core.database import AsyncSessionLocal
from app.core.media import delete_media
from app.enums.product_status import ProductStatusEnum
from app.models import Category, OrderLine, Product, Supplier, SupplierCategory, SupplierOffer
from app.services.partner_catalog_service import PartnerCatalogService
from app.services.pricing_service import PricingService

DEMO_CATEGORY_SLUGS = [
    "shtukaturka",
    "shpaklevka",
    "gipsokarton",
    "profil",
    "shumoizolyatsiya",
    "pol",
    "plitka",
    "kraski",
    "elektrika",
    "osvescheniya",
    "montazh",
]
OLD_PREFIX = "old-"


async def find_demo(db) -> tuple[list[Category], list[Product]]:
    # Импорт мог завести раздел партнёра с тем же адресом, например «shpaklevka».
    # Такие разделы привязаны к категориям партнёра, их не трогаем
    partner_categories = select(SupplierCategory.category_id).where(SupplierCategory.category_id.is_not(None))
    categories = list(
        await db.scalars(
            select(Category).where(
                or_(Category.slug.in_(DEMO_CATEGORY_SLUGS), Category.slug.startswith(OLD_PREFIX)),
                Category.id.not_in(partner_categories),
            )
        )
    )
    # До первого импорта дерева партнёра товары партнёра заводил только демо-скрипт
    tree_since = await db.scalar(select(func.min(SupplierCategory.created_at)))
    partner_products = select(SupplierOffer.product_id).where(SupplierOffer.product_id.is_not(None))
    if tree_since is not None:
        partner_products = partner_products.join(Product, Product.id == SupplierOffer.product_id).where(
            Product.created_at < tree_since
        )

    conditions = [Product.sku.startswith("DEMO-"), Product.id.in_(partner_products)]
    if categories:
        conditions.append(Product.category_id.in_([category.id for category in categories]))
    # Уже убранные в архив не считаем, чтобы повторный запуск ничего не находил
    products = list(
        await db.scalars(
            select(Product)
            .where(or_(*conditions), Product.status != ProductStatusEnum.archived.value)
            .order_by(Product.id)
        )
    )
    return categories, products


async def main(apply: bool) -> int:
    async with AsyncSessionLocal() as db:
        categories, products = await find_demo(db)
        ordered = set(
            await db.scalars(
                select(OrderLine.product_id)
                .where(OrderLine.product_id.in_([product.id for product in products]))
                .distinct()
            )
        )
        to_delete = [product for product in products if product.id not in ordered]
        to_archive = [product for product in products if product.id in ordered]

        print(f"Демо-товаров найдено: {len(products)}")
        print(f"  удалить: {len(to_delete)}")
        print(f"  в архив (есть в заказах): {len(to_archive)}")
        for product in to_archive:
            print(f"    {product.sku} {product.name}")
        print(
            f"Демо-разделов: {len(categories)} — {', '.join(category.name for category in categories) or 'нет'}"
        )

        if not apply:
            print("\nЭто проверка, ничего не изменено. Чтобы удалить: python -m scripts.cleanup_demo --apply")
            return 0

        images = [image for product in to_delete for image in product.images]
        for product in to_archive:
            product.status = ProductStatusEnum.archived.value
        if to_archive:
            # Отвязываем от партнёра, иначе импорт не заведёт вместо архивного новый товар
            offers = await db.scalars(
                select(SupplierOffer).where(
                    SupplierOffer.product_id.in_([product.id for product in to_archive])
                )
            )
            for offer in offers:
                offer.product_id = None
        for product in to_delete:
            await db.delete(product)
        await db.flush()

        # Сначала подразделы, потом разделы; раздел с архивными товарами остаётся скрытым
        deleted_categories = 0
        for category in sorted(categories, key=lambda item: item.parent_id is None):
            products_left = await db.scalar(
                select(func.count(Product.id)).where(Product.category_id == category.id)
            )
            children = await db.scalar(
                select(func.count(Category.id)).where(Category.parent_id == category.id)
            )
            if products_left or children:
                category.is_active = False
                if not category.slug.startswith(OLD_PREFIX):
                    category.slug = OLD_PREFIX + category.slug
                continue
            # Импорт больше не должен направлять сюда товары партнёра
            mapped = await db.scalars(
                select(SupplierCategory).where(SupplierCategory.category_id == category.id)
            )
            for row in mapped:
                row.category_id = None
            await db.delete(category)
            await db.flush()
            deleted_categories += 1
        await db.commit()

        # Фото удаляем после commit: если что-то сорвалось, товары остались бы без картинок
        for image in images:
            delete_media(image)
        print(
            f"\nУдалено товаров: {len(to_delete)}, в архиве: {len(to_archive)}, удалено разделов: {deleted_categories}"
        )

        created = 0
        for supplier in await db.scalars(
            select(Supplier).where(Supplier.is_active.is_(True), Supplier.show_on_storefront.is_(True))
        ):
            created += await PartnerCatalogService(db=db).create_products(supplier=supplier)
        if created:
            await PricingService(db=db).recalc_prices()
            await db.commit()
            print(f"Импорт заново завёл товаров партнёра: {created}")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="удалить, а не только показать")
    sys.exit(asyncio.run(main(apply=parser.parse_args().apply)))
