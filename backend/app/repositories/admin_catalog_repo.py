from decimal import Decimal

from sqlalchemy import func, or_, select

from app.models.catalog import Category, Product
from app.models.inventory import StockItem, Supplier, SupplierOffer, Warehouse
from app.repositories.base_repo import BaseRepository


class AdminCatalogRepository(BaseRepository):

    # ─── Категории ────────────────────────────────────────────────────────────

    async def get_categories_with_counts(self) -> list[tuple[Category, int]]:
        counts = (
            select(Product.category_id, func.count(Product.id).label("count"))
            .group_by(Product.category_id)
            .subquery()
        )
        result = await self.db.execute(
            select(Category, func.coalesce(counts.c.count, 0))
            .outerjoin(counts, counts.c.category_id == Category.id)
            .order_by(Category.position, Category.name)
        )
        return [(category, count) for category, count in result.all()]

    async def get_category(self, category_id: int) -> Category | None:
        return await self.db.get(Category, category_id)

    async def category_slug_exists(self, slug: str, exclude_id: int | None = None) -> bool:
        query = select(Category.id).where(Category.slug == slug)
        if exclude_id is not None:
            query = query.where(Category.id != exclude_id)
        result = await self.db.execute(query.limit(1))
        return result.scalar() is not None

    async def count_category_products(self, category_id: int) -> int:
        result = await self.db.execute(
            select(func.count(Product.id)).where(Product.category_id == category_id)
        )
        return result.scalar() or 0

    async def create_category(self, **values) -> Category:
        category = Category(**values)
        self.db.add(category)
        await self.db.flush()
        await self.db.refresh(category)
        return category

    async def delete_category(self, category: Category) -> None:
        await self.db.delete(category)
        await self.db.flush()

    # ─── Товары ───────────────────────────────────────────────────────────────

    async def get_products(
        self,
        search: str | None = None,
        category_id: int | None = None,
        status: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[tuple[Product, Decimal, Decimal | None, Decimal | None]], int]:
        """Товары с доступным остатком склада и лучшим предложением партнёра."""
        stock = (
            select(
                StockItem.product_id,
                func.sum(StockItem.quantity - StockItem.reserved).label("quantity"),
            )
            .group_by(StockItem.product_id)
            .subquery()
        )
        # Сначала предложение с остатком, потом самое дешёвое
        offer = (
            select(SupplierOffer.product_id, SupplierOffer.price, SupplierOffer.quantity)
            .where(SupplierOffer.is_active == True, SupplierOffer.product_id.is_not(None))  # noqa: E712
            .distinct(SupplierOffer.product_id)
            .order_by(SupplierOffer.product_id, (SupplierOffer.quantity > 0).desc(), SupplierOffer.price)
            .subquery()
        )

        conditions = []
        if search:
            conditions.append(
                or_(
                    Product.name.icontains(search, autoescape=True),
                    Product.sku.icontains(search, autoescape=True),
                )
            )
        if category_id is not None:
            conditions.append(Product.category_id == category_id)
        if status:
            conditions.append(Product.status == status)

        total = await self.db.execute(select(func.count(Product.id)).where(*conditions))
        result = await self.db.execute(
            select(Product, func.coalesce(stock.c.quantity, 0), offer.c.price, offer.c.quantity)
            .outerjoin(stock, stock.c.product_id == Product.id)
            .outerjoin(offer, offer.c.product_id == Product.id)
            .where(*conditions)
            .order_by(Product.updated_at.desc(), Product.id.desc())
            .offset(skip)
            .limit(limit)
        )
        return [tuple(row) for row in result.all()], total.scalar() or 0

    async def get_product(self, product_id: int) -> Product | None:
        return await self.db.get(Product, product_id)

    async def product_field_exists(self, field: str, value: str, exclude_id: int | None = None) -> bool:
        column = getattr(Product, field)
        query = select(Product.id).where(column == value)
        if exclude_id is not None:
            query = query.where(Product.id != exclude_id)
        result = await self.db.execute(query.limit(1))
        return result.scalar() is not None

    async def create_product(self, **values) -> Product:
        product = Product(**values)
        self.db.add(product)
        await self.db.flush()
        await self.db.refresh(product)
        return product

    async def get_product_offers(self, product_id: int) -> list[tuple[SupplierOffer, str]]:
        result = await self.db.execute(
            select(SupplierOffer, Supplier.name)
            .join(Supplier, Supplier.id == SupplierOffer.supplier_id)
            .where(SupplierOffer.product_id == product_id)
            .order_by(SupplierOffer.is_active.desc(), SupplierOffer.price)
        )
        return [(offer, name) for offer, name in result.all()]

    # ─── Склад ────────────────────────────────────────────────────────────────

    async def get_warehouses(self) -> list[Warehouse]:
        result = await self.db.execute(
            select(Warehouse).where(Warehouse.is_active == True).order_by(Warehouse.id)  # noqa: E712
        )
        return list(result.scalars().all())

    async def get_warehouse(self, warehouse_id: int) -> Warehouse | None:
        return await self.db.get(Warehouse, warehouse_id)

    async def get_product_stock(self, product_id: int) -> list[tuple[StockItem, str]]:
        result = await self.db.execute(
            select(StockItem, Warehouse.name)
            .join(Warehouse, Warehouse.id == StockItem.warehouse_id)
            .where(StockItem.product_id == product_id)
            .order_by(Warehouse.id)
        )
        return [(item, name) for item, name in result.all()]

    async def get_stock_item_for_update(self, warehouse_id: int, product_id: int) -> StockItem | None:
        result = await self.db.execute(
            select(StockItem)
            .where(StockItem.warehouse_id == warehouse_id, StockItem.product_id == product_id)
            .with_for_update()
        )
        return result.scalar_one_or_none()

    async def create_stock_item(self, **values) -> StockItem:
        item = StockItem(**values)
        self.db.add(item)
        await self.db.flush()
        return item
