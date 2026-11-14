"""
Разовый перенос демо-каталога в разделы партнёра.

Демо-разделы (11 штук, их заводил демо-скрипт в ноябре 2026) освобождают свои адреса и
скрываются. Товары партнёра из них переезжают в разделы по дереву выгрузки, опустевшие
демо-разделы удаляются. Повторный запуск безопасен.

Запуск: python -m scripts.retire_demo_catalog
"""

import asyncio
import sys

from sqlalchemy import func, select

from app.core.database import AsyncSessionLocal
from app.models import Category, Product, Supplier, SupplierOffer
from app.services.partner_catalog_service import PartnerCatalogService
from app.services.pricing_service import PricingService
from app.services.supplier_service import SupplierService

SUPPLIER_CODE = "famarket"
OLD_PREFIX = "old-"
DEMO_SLUGS = [
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


async def main() -> int:
    async with AsyncSessionLocal() as db:
        supplier = await db.scalar(select(Supplier).where(Supplier.code == SUPPLIER_CODE))
        if supplier is None:
            print("Поставщик famarket не найден", file=sys.stderr)
            return 1
        supplier_id = supplier.id

        # Освобождаем адреса до того, как импорт заведёт разделы партнёра с такими же именами
        slugs = DEMO_SLUGS + [OLD_PREFIX + slug for slug in DEMO_SLUGS]
        demo = list(await db.scalars(select(Category).where(Category.slug.in_(slugs))))
        for category in demo:
            if not category.slug.startswith(OLD_PREFIX):
                category.slug = OLD_PREFIX + category.slug
            category.is_active = False
        await db.commit()
        demo_ids = [category.id for category in demo]
        print(f"Демо-разделов скрыто: {len(demo)}")

    # Для переноса нужно свежее дерево категорий партнёра
    async with AsyncSessionLocal() as db:
        result = await SupplierService(db=db).sync_supplier(supplier_id=supplier_id)
        if not result.ok:
            print(f"Импорт не удался: {result.error}", file=sys.stderr)
            return 1
        print(f"Импорт: {result.supplier.last_sync_summary}")

    async with AsyncSessionLocal() as db:
        resolver = await PartnerCatalogService(db=db).category_resolver(supplier_id)
        rows = await db.execute(
            select(Product, SupplierOffer.category_external_id)
            .join(SupplierOffer, SupplierOffer.product_id == Product.id)
            .where(SupplierOffer.supplier_id == supplier_id, Product.category_id.in_(demo_ids))
        )
        moved: set[int] = set()
        for product, category_external_id in rows.all():
            category_id = await resolver.resolve(category_external_id)
            if category_id is not None:
                product.category_id = category_id
                moved.add(product.id)
        await db.flush()
        # Правило наценки могло быть на старом разделе
        await PricingService(db=db).recalc_prices(product_ids=list(moved))

        # Сначала подразделы, потом разделы
        deleted = 0
        for category in sorted(demo, key=lambda item: item.parent_id is None):
            products = await db.scalar(
                select(func.count(Product.id)).where(Product.category_id == category.id)
            )
            children = await db.scalar(
                select(func.count(Category.id)).where(Category.parent_id == category.id)
            )
            if not products and not children:
                await db.delete(category)
                await db.flush()
                deleted += 1
        await db.commit()

    print(f"Перенесено товаров: {len(moved)}, удалено пустых демо-разделов: {deleted}")
    left = len(demo) - deleted
    if left:
        print(f"Осталось скрытых демо-разделов с товарами: {left}, разберите их в админке")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
