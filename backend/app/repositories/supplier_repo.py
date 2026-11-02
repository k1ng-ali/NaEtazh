from sqlalchemy import case, func, or_, select

from app.models.catalog import Product
from app.models.inventory import Supplier, SupplierOffer
from app.repositories.base_repo import BaseRepository


class SupplierRepository(BaseRepository):

    async def get_suppliers_with_counts(self) -> list[tuple[Supplier, int, int]]:
        """Поставщики с числом активных и несопоставленных активных предложений."""
        active = SupplierOffer.is_active == True  # noqa: E712
        counts = (
            select(
                SupplierOffer.supplier_id,
                func.count(case((active, 1))).label("active"),
                func.count(case((active & SupplierOffer.product_id.is_(None), 1))).label("unmatched"),
            )
            .group_by(SupplierOffer.supplier_id)
            .subquery()
        )
        result = await self.db.execute(
            select(Supplier, func.coalesce(counts.c.active, 0), func.coalesce(counts.c.unmatched, 0))
            .outerjoin(counts, counts.c.supplier_id == Supplier.id)
            .order_by(Supplier.id)
        )
        return [(supplier, active_count, unmatched) for supplier, active_count, unmatched in result.all()]

    async def get_supplier(self, supplier_id: int) -> Supplier | None:
        return await self.db.get(Supplier, supplier_id)

    async def get_supplier_for_update(self, supplier_id: int) -> Supplier | None:
        # Блокировка не даёт двум импортам одного поставщика идти одновременно
        result = await self.db.execute(
            select(Supplier).where(Supplier.id == supplier_id).with_for_update(nowait=True)
        )
        return result.scalar_one_or_none()

    async def get_active_supplier_ids(self) -> list[int]:
        result = await self.db.execute(
            select(Supplier.id).where(
                Supplier.is_active == True,  # noqa: E712
                Supplier.feed_url.is_not(None),
            )
        )
        return list(result.scalars().all())

    async def get_supplier_offers(self, supplier_id: int) -> list[SupplierOffer]:
        result = await self.db.execute(select(SupplierOffer).where(SupplierOffer.supplier_id == supplier_id))
        return list(result.scalars().all())

    async def add_offers(self, offers: list[SupplierOffer]) -> None:
        self.db.add_all(offers)
        await self.db.flush()

    async def get_offers(
        self,
        supplier_id: int | None = None,
        match: str = "all",
        search: str | None = None,
        in_stock: bool = False,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[tuple[SupplierOffer, str | None]], int]:
        conditions = [SupplierOffer.is_active == True]  # noqa: E712
        if supplier_id is not None:
            conditions.append(SupplierOffer.supplier_id == supplier_id)
        if match == "unmatched":
            conditions.append(SupplierOffer.product_id.is_(None))
        elif match == "matched":
            conditions.append(SupplierOffer.product_id.is_not(None))
        if search:
            conditions.append(
                or_(
                    SupplierOffer.name.icontains(search, autoescape=True),
                    SupplierOffer.vendor.icontains(search, autoescape=True),
                    SupplierOffer.category_name.icontains(search, autoescape=True),
                    SupplierOffer.external_id == search,
                )
            )
        if in_stock:
            conditions.append(SupplierOffer.quantity > 0)

        total = await self.db.execute(select(func.count(SupplierOffer.id)).where(*conditions))
        result = await self.db.execute(
            select(SupplierOffer, Product.name)
            .outerjoin(Product, Product.id == SupplierOffer.product_id)
            .where(*conditions)
            .order_by(SupplierOffer.category_name, SupplierOffer.name, SupplierOffer.id)
            .offset(skip)
            .limit(limit)
        )
        return [(offer, product_name) for offer, product_name in result.all()], total.scalar() or 0

    async def get_offer(self, offer_id: int) -> SupplierOffer | None:
        return await self.db.get(SupplierOffer, offer_id)

    async def get_product(self, product_id: int) -> Product | None:
        return await self.db.get(Product, product_id)
