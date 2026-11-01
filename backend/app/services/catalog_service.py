from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.catalog_repo import CatalogRepository
from app.schemas.catalog import CategoryOut, ProductListOut, ProductOut


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

    async def get_product(self, slug: str) -> ProductOut:
        product = await self.repo.get_published_product_by_slug(slug=slug)
        if product is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        return ProductOut.model_validate(product)
