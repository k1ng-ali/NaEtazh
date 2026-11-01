from sqlalchemy import func, select

from app.enums.product_status import ProductStatusEnum
from app.models.catalog import Category, Product
from app.repositories.base_repo import BaseRepository


class CatalogRepository(BaseRepository):

    async def get_active_categories(self) -> list[Category]:
        result = await self.db.execute(
            select(Category)
            .where(Category.is_active == True)  # noqa: E712
            .order_by(Category.position, Category.name)
        )
        return list(result.scalars().all())

    async def get_published_products(
        self,
        category_slug: str | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[Product], int]:
        conditions = [Product.status == ProductStatusEnum.published.value]
        if category_slug:
            conditions.append(
                Product.category_id.in_(select(Category.id).where(Category.slug == category_slug))
            )
        if search:
            conditions.append(Product.name.icontains(search, autoescape=True))

        total = await self.db.execute(select(func.count(Product.id)).where(*conditions))
        result = await self.db.execute(
            select(Product).where(*conditions).order_by(Product.name).offset(skip).limit(limit)
        )
        return list(result.scalars().all()), total.scalar() or 0

    async def get_published_product_by_slug(self, slug: str) -> Product | None:
        result = await self.db.execute(
            select(Product).where(
                Product.slug == slug,
                Product.status == ProductStatusEnum.published.value,
            )
        )
        return result.scalar_one_or_none()
