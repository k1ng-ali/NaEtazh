from sqlalchemy import func, select

from app.models.catalog import Category, Product
from app.models.inventory import Supplier, SupplierCategory, SupplierOffer
from app.repositories.base_repo import BaseRepository


class PartnerCatalogRepository(BaseRepository):

    async def get_supplier_categories(self, supplier_id: int) -> list[SupplierCategory]:
        result = await self.db.execute(
            select(SupplierCategory).where(SupplierCategory.supplier_id == supplier_id)
        )
        return list(result.scalars().all())

    async def get_offers_without_product(self, supplier_id: int) -> list[SupplierOffer]:
        """Активные предложения без товара витрины, сначала те, что в наличии."""
        result = await self.db.execute(
            select(SupplierOffer)
            .where(
                SupplierOffer.supplier_id == supplier_id,
                SupplierOffer.is_active == True,  # noqa: E712
                SupplierOffer.product_id.is_(None),
            )
            .order_by((SupplierOffer.quantity > 0).desc(), SupplierOffer.id)
        )
        return list(result.scalars().all())

    async def get_category_slugs(self) -> set[str]:
        return set((await self.db.execute(select(Category.slug))).scalars().all())

    async def get_next_category_position(self) -> int:
        return (await self.db.scalar(select(func.max(Category.position)))) or 0

    async def get_product_slugs_and_skus(self) -> tuple[set[str], set[str]]:
        rows = (await self.db.execute(select(Product.slug, Product.sku))).all()
        return {slug for slug, _ in rows}, {sku for _, sku in rows}

    async def get_products_without_photo(self, limit: int) -> list[tuple[Product, str]]:
        """Товары поставщиков без своих фото, у которых в выгрузке есть фото. Сначала в наличии."""
        in_stock = (SupplierOffer.quantity > 0).label("in_stock")
        best = (
            select(SupplierOffer.product_id, SupplierOffer.picture_url, in_stock)
            .join(Supplier, Supplier.id == SupplierOffer.supplier_id)
            .where(
                Supplier.is_active == True,  # noqa: E712
                SupplierOffer.is_active == True,  # noqa: E712
                SupplierOffer.product_id.is_not(None),
                SupplierOffer.picture_url.is_not(None),
            )
            .distinct(SupplierOffer.product_id)
            .order_by(SupplierOffer.product_id, in_stock.desc())
            .subquery()
        )
        result = await self.db.execute(
            select(Product, best.c.picture_url)
            .join(best, best.c.product_id == Product.id)
            .where(func.jsonb_array_length(Product.images) == 0)
            .order_by(best.c.in_stock.desc(), Product.id)
            .limit(limit)
        )
        return [(product, picture_url) for product, picture_url in result.all()]
