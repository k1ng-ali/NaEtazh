from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums.availability import AvailabilityEnum
from app.repositories.catalog_repo import CatalogRepository
from app.repositories.order_repo import OrderRepository
from app.repositories.pricing_repo import PricingRepository
from app.schemas.catalog import CategoryOut, ProductDetailOut, ProductListOut, ProductOut


class CatalogService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = CatalogRepository(db=db)

    async def list_categories(self) -> list[CategoryOut]:
        """Включённые разделы, где есть что купить, вместе с их родителями."""
        categories = await self.repo.get_active_categories()
        by_id = {category.id: category for category in categories}
        visible: set[int] = set()
        photos = await self.repo.get_category_photos()
        # Лучшее фото раздела — среди него самого и всех подразделов
        best: dict[int, tuple[str, float]] = {}
        for category_id, photo in photos.items():
            current = by_id.get(category_id)
            seen: set[int] = set()
            while current is not None and current.id not in seen:
                seen.add(current.id)
                if current.id not in best or photo[1] > best[current.id][1]:
                    best[current.id] = photo
                current = by_id.get(current.parent_id) if current.parent_id is not None else None

        for category_id in await self.repo.get_visible_category_ids():
            # Подраздел выключенного раздела не показываем
            chain, current = [], by_id.get(category_id)
            while current is not None:
                chain.append(current.id)
                if current.parent_id is None:
                    visible.update(chain)
                    break
                current = by_id.get(current.parent_id)
        return [
            CategoryOut.model_validate(item).model_copy(
                update={"image": item.image or (best[item.id][0] if item.id in best else None)}
            )
            for item in categories
            if item.id in visible
        ]

    async def list_products(
        self,
        category_slug: str | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> ProductListOut:
        items, total = await self.repo.get_published_products(
            category_slug=category_slug,
            search=search,
            skip=skip,
            limit=limit,
        )
        return ProductListOut(items=[ProductOut.model_validate(item) for item in items], total=total)

    async def get_product(self, slug: str) -> ProductDetailOut:
        product = await self.repo.get_published_product_by_slug(slug=slug)
        if product is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

        # Покупатель видит только «в наличии» или «под заказ», источник не раскрываем
        stock = await OrderRepository(db=self.db).get_stock_available([product.id])
        offers = await PricingRepository(db=self.db).get_sellable_offers([product])
        offer = offers.get(product.id)
        if stock.get(product.id, 0) > 0:
            availability = AvailabilityEnum.in_stock
        elif offer is not None and offer.quantity > 0:
            availability = AvailabilityEnum.on_order
        else:
            availability = AvailabilityEnum.unavailable
        return ProductDetailOut(**ProductOut.model_validate(product).model_dump(), availability=availability)
