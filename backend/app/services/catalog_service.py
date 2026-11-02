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
        items = await self.repo.get_active_categories()
        return [CategoryOut.model_validate(item) for item in items]

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
        offers = await PricingRepository(db=self.db).get_best_offers([product.id])
        offer = offers.get(product.id)
        if stock.get(product.id, 0) > 0:
            availability = AvailabilityEnum.in_stock
        elif offer is not None and offer.quantity > 0:
            availability = AvailabilityEnum.on_order
        else:
            availability = AvailabilityEnum.unavailable
        return ProductDetailOut(**ProductOut.model_validate(product).model_dump(), availability=availability)
