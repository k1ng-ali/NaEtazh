"""
Витрина из выгрузки поставщика.

Разделы витрины повторяют два верхних уровня дерева категорий поставщика, более глубокие
категории попадают в свой подраздел. Товары заводятся опубликованными с автоматической ценой.
Покупатель видит товар, когда поставщик включён на витрине, товар есть в наличии и для него
задана наценка, — это проверяет каталог при каждом запросе.
"""

import asyncio
import logging
import re

import httpx
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.media import MAX_UPLOAD_BYTES, InvalidImageError, compress_image, save_media
from app.core.slug import slugify
from app.core.yml_feed import FeedCategory
from app.enums.product_status import ProductStatusEnum
from app.models.catalog import Category, Product
from app.models.inventory import Supplier, SupplierCategory
from app.repositories.partner_catalog_repo import PartnerCatalogRepository

logger = logging.getLogger(__name__)

# Глубже второго уровня разделы не дробим: на телефоне такое дерево не пролистать
MAX_DEPTH = 2
# Служебные разделы поставщика заводим скрытыми, менеджер включит, если нужно
_SERVICE_CATEGORY_RE = re.compile(r"акци|распродаж|под типы", re.IGNORECASE)
# Поставщик не должен заметить нагрузку
PHOTO_PAUSE_S = 0.2
PHOTO_TIMEOUT_S = 20
PHOTO_COMMIT_EVERY = 50


def unique_value(base: str, taken: set[str]) -> str:
    value, suffix = base, 2
    while value in taken:
        value, suffix = f"{base}-{suffix}", suffix + 1
    taken.add(value)
    return value


class CategoryResolver:
    """Находит раздел витрины для категории поставщика и заводит недостающие разделы."""

    def __init__(self, db: AsyncSession, rows: list[SupplierCategory], slugs: set[str], position: int):
        self.db = db
        self.rows = {row.external_id: row for row in rows}
        self.slugs = slugs
        self.position = position

    def chain(self, row: SupplierCategory) -> list[SupplierCategory]:
        """Путь от корня дерева до категории."""
        chain, seen = [row], {row.external_id}
        while (
            parent := self.rows.get(chain[-1].parent_external_id or "")
        ) and parent.external_id not in seen:
            chain.append(parent)
            seen.add(parent.external_id)
        return chain[::-1]

    async def resolve(self, external_id: str | None) -> int | None:
        row = self.rows.get(external_id or "")
        if row is None:
            return None
        # Раздел уже заведён или менеджер направил категорию в свой раздел
        if row.category_id is not None:
            return row.category_id

        chain = self.chain(row)
        if len(chain) > MAX_DEPTH:
            return await self.resolve(chain[MAX_DEPTH - 1].external_id)
        parent_id = await self.resolve(chain[-2].external_id) if len(chain) > 1 else None

        self.position += 1
        category = Category(
            name=row.name,
            slug=unique_value(slugify(row.name), self.slugs),
            parent_id=parent_id,
            position=self.position,
            is_active=not _SERVICE_CATEGORY_RE.search(row.name),
        )
        self.db.add(category)
        await self.db.flush()
        row.category_id = category.id
        return category.id


class PartnerCatalogService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = PartnerCatalogRepository(db=db)

    async def save_categories(self, supplier_id: int, categories: list[FeedCategory]) -> None:
        """Сохраняет дерево категорий поставщика. Не делает commit."""
        existing = {row.external_id: row for row in await self.repo.get_supplier_categories(supplier_id)}
        for item in categories:
            row = existing.get(item.external_id)
            if row is None:
                self.db.add(
                    SupplierCategory(
                        supplier_id=supplier_id,
                        external_id=item.external_id,
                        parent_external_id=item.parent_external_id,
                        name=item.name,
                    )
                )
            else:
                row.name = item.name
                row.parent_external_id = item.parent_external_id
        await self.db.flush()

    async def category_resolver(self, supplier_id: int) -> CategoryResolver:
        return CategoryResolver(
            db=self.db,
            rows=await self.repo.get_supplier_categories(supplier_id),
            slugs=await self.repo.get_category_slugs(),
            position=await self.repo.get_next_category_position(),
        )

    async def create_products(self, supplier: Supplier) -> int:
        """
        Заводит товары витрины для всех предложений без товара. Не делает commit.

        Фото здесь не качаются, чтобы импорт по кнопке не ждал минутами: их добирает
        fill_missing_photos из импорта по расписанию.
        """
        offers = await self.repo.get_offers_without_product(supplier_id=supplier.id)
        if not offers:
            return 0
        resolver = await self.category_resolver(supplier.id)
        slugs, skus = await self.repo.get_product_slugs_and_skus()
        sku_prefix = supplier.code[:2].upper()

        pairs = []
        for offer in offers:
            category_id = await resolver.resolve(offer.category_external_id)
            # Без категории товару некуда встать, менеджер заведёт его вручную
            if category_id is None:
                continue
            product = Product(
                category_id=category_id,
                sku=unique_value(f"{sku_prefix}-{offer.external_id}", skus),
                name=offer.name,
                slug=unique_value(slugify(offer.name), slugs),
                unit="шт",
                # Цену по наценке ставит пересчёт после импорта
                price=offer.price,
                is_price_manual=False,
                weight_kg=offer.weight_kg,
                images=[],
                attributes={"Бренд": offer.vendor} if offer.vendor else {},
                status=ProductStatusEnum.published.value,
            )
            pairs.append((offer, product))

        self.db.add_all([product for _, product in pairs])
        await self.db.flush()
        for offer, product in pairs:
            offer.product_id = product.id
        await self.db.flush()
        return len(pairs)

    async def fill_missing_photos(self, limit: int) -> tuple[int, int]:
        """Копирует фото поставщика к себе в WebP. Возвращает, сколько сохранено и сколько не скачалось."""
        rows = await self.repo.get_products_without_photo(limit=limit)
        saved = failed = 0
        async with httpx.AsyncClient(
            timeout=PHOTO_TIMEOUT_S,
            follow_redirects=True,
            headers={"User-Agent": "StroyBaza catalog import"},
        ) as client:
            for index, (product, url) in enumerate(rows, start=1):
                image = await self._download_photo(client, url)
                if image is None:
                    failed += 1
                else:
                    product.images = [image]
                    saved += 1
                if index % PHOTO_COMMIT_EVERY == 0:
                    await self.db.commit()
                await asyncio.sleep(PHOTO_PAUSE_S)
        await self.db.commit()
        return saved, failed

    @staticmethod
    async def _download_photo(client: httpx.AsyncClient, url: str) -> str | None:
        try:
            response = await client.get(url)
            response.raise_for_status()
            if len(response.content) > MAX_UPLOAD_BYTES:
                raise InvalidImageError("Image is too large")
            compressed = await run_in_threadpool(compress_image, response.content)
        except (httpx.HTTPError, InvalidImageError) as exc:
            logger.warning("Фото не скачалось: %s (%s)", url, type(exc).__name__)
            return None
        return await run_in_threadpool(save_media, compressed, "products")
