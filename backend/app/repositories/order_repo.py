from decimal import Decimal

from sqlalchemy import exists, func, or_, select

from app.enums.order import AllocationSourceEnum
from app.models.catalog import Product
from app.models.inventory import StockItem, Supplier, SupplierOffer, Warehouse
from app.models.order import Order, OrderAllocation, OrderLine, OrderServiceLine
from app.repositories.base_repo import BaseRepository


class OrderRepository(BaseRepository):

    # ─── Товары и наличие ─────────────────────────────────────────────────────

    async def get_products(self, product_ids: list[int]) -> dict[int, Product]:
        result = await self.db.execute(select(Product).where(Product.id.in_(product_ids)))
        return {product.id: product for product in result.scalars().all()}

    async def get_stock_available(self, product_ids: list[int]) -> dict[int, Decimal]:
        """Свободный остаток своих складов: всего минус резерв под заказы."""
        result = await self.db.execute(
            select(StockItem.product_id, func.sum(StockItem.quantity - StockItem.reserved))
            .join(Warehouse, Warehouse.id == StockItem.warehouse_id)
            .where(StockItem.product_id.in_(product_ids), Warehouse.is_active == True)  # noqa: E712
            .group_by(StockItem.product_id)
        )
        return {product_id: max(quantity, Decimal("0")) for product_id, quantity in result.all()}

    async def get_stock_items_for_update(self, product_id: int) -> list[StockItem]:
        result = await self.db.execute(
            select(StockItem)
            .join(Warehouse, Warehouse.id == StockItem.warehouse_id)
            .where(StockItem.product_id == product_id, Warehouse.is_active == True)  # noqa: E712
            .order_by(StockItem.warehouse_id)
            .with_for_update(of=StockItem)
        )
        return list(result.scalars().all())

    # ─── Создание ─────────────────────────────────────────────────────────────

    async def add(self, item) -> None:
        self.db.add(item)
        await self.db.flush()

    # ─── Чтение ───────────────────────────────────────────────────────────────

    async def get_order_by_token(self, token: str) -> Order | None:
        result = await self.db.execute(select(Order).where(Order.public_token == token))
        return result.scalar_one_or_none()

    async def get_order(self, order_id: int) -> Order | None:
        return await self.db.get(Order, order_id)

    async def get_order_for_update(self, order_id: int) -> Order | None:
        result = await self.db.execute(select(Order).where(Order.id == order_id).with_for_update())
        return result.scalar_one_or_none()

    async def get_lines(self, order_id: int) -> list[OrderLine]:
        result = await self.db.execute(
            select(OrderLine).where(OrderLine.order_id == order_id).order_by(OrderLine.id)
        )
        return list(result.scalars().all())

    async def get_services(self, order_id: int) -> list[OrderServiceLine]:
        result = await self.db.execute(
            select(OrderServiceLine)
            .where(OrderServiceLine.order_id == order_id)
            .order_by(OrderServiceLine.id)
        )
        return list(result.scalars().all())

    async def get_service(self, service_id: int) -> OrderServiceLine | None:
        return await self.db.get(OrderServiceLine, service_id)

    async def get_allocations(
        self, line_ids: list[int]
    ) -> list[tuple[OrderAllocation, str | None, str | None, str | None]]:
        """Распределение с названием склада или поставщика и ссылкой на товар партнёра."""
        if not line_ids:
            return []
        result = await self.db.execute(
            select(OrderAllocation, Warehouse.name, Supplier.name, SupplierOffer.url)
            .outerjoin(Warehouse, Warehouse.id == OrderAllocation.warehouse_id)
            .outerjoin(SupplierOffer, SupplierOffer.id == OrderAllocation.supplier_offer_id)
            .outerjoin(Supplier, Supplier.id == SupplierOffer.supplier_id)
            .where(OrderAllocation.order_line_id.in_(line_ids))
            .order_by(OrderAllocation.id)
        )
        return [tuple(row) for row in result.all()]

    async def get_warehouse_allocations_for_update(
        self, order_id: int
    ) -> list[tuple[OrderAllocation, StockItem]]:
        result = await self.db.execute(
            select(OrderAllocation, StockItem)
            .join(OrderLine, OrderLine.id == OrderAllocation.order_line_id)
            .join(
                StockItem,
                (StockItem.warehouse_id == OrderAllocation.warehouse_id)
                & (StockItem.product_id == OrderLine.product_id),
            )
            .where(
                OrderLine.order_id == order_id,
                OrderAllocation.source_type == AllocationSourceEnum.warehouse.value,
            )
            .with_for_update(of=StockItem)
        )
        return [(allocation, stock) for allocation, stock in result.all()]

    async def get_orders(
        self,
        status: str | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[tuple[Order, bool]], int]:
        conditions = []
        if status:
            conditions.append(Order.status == status)
        if search:
            digits = "".join(char for char in search if char.isdigit())
            options = [Order.customer_name.icontains(search, autoescape=True)]
            if digits:
                options.append(Order.customer_phone.contains(digits, autoescape=True))
                if len(digits) <= 9:
                    options.append(Order.id == int(digits))
            conditions.append(or_(*options))

        has_supplier = exists(
            select(OrderAllocation.id)
            .join(OrderLine, OrderLine.id == OrderAllocation.order_line_id)
            .where(
                OrderLine.order_id == Order.id,
                OrderAllocation.source_type == AllocationSourceEnum.supplier.value,
            )
        )
        total = await self.db.execute(select(func.count(Order.id)).where(*conditions))
        result = await self.db.execute(
            select(Order, has_supplier)
            .where(*conditions)
            .order_by(Order.created_at.desc(), Order.id.desc())
            .offset(skip)
            .limit(limit)
        )
        return [(order, flag) for order, flag in result.all()], total.scalar() or 0
