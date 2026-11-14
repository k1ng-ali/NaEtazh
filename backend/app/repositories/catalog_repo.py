from sqlalchemy import ColumnElement, Select, and_, func, or_, select

from app.enums.product_status import ProductStatusEnum
from app.models.catalog import Category, Product
from app.models.inventory import StockItem, Supplier, SupplierOffer, Warehouse
from app.models.pricing import PricingRule
from app.repositories.base_repo import BaseRepository


def _active_category_ids() -> Select:
    """Включённые разделы, у которых включены и все родители."""
    tree = (
        select(Category.id)
        .where(Category.parent_id.is_(None), Category.is_active == True)  # noqa: E712
        .cte("active_categories", recursive=True)
    )
    tree = tree.union_all(
        select(Category.id)
        .join(tree, Category.parent_id == tree.c.id)
        .where(Category.is_active == True)  # noqa: E712
    )
    return select(tree.c.id)


def _category_subtree_ids(slug: str) -> Select:
    """Раздел и все его подразделы."""
    tree = select(Category.id).where(Category.slug == slug).cte("category_subtree", recursive=True)
    tree = tree.union_all(select(Category.id).join(tree, Category.parent_id == tree.c.id))
    return select(tree.c.id)


def partner_picture():
    """Фото товара в выгрузке поставщика: сначала у предложения в наличии."""
    return (
        select(SupplierOffer.picture_url)
        .where(
            SupplierOffer.product_id == Product.id,
            SupplierOffer.is_active == True,  # noqa: E712
            SupplierOffer.picture_url.is_not(None),
        )
        .order_by((SupplierOffer.quantity > 0).desc(), SupplierOffer.id)
        .limit(1)
        .scalar_subquery()
    )


def product_picture():
    """Своё фото, а пока импорт его не скачал — фото поставщика по ссылке."""
    return func.coalesce(Product.images[0].astext, partner_picture())


def visible_product_conditions() -> list[ColumnElement[bool]]:
    """
    Товар виден покупателю: опубликован, раздел включён и товар можно купить.

    Купить можно со своего склада или у поставщика, включённого на витрине. Товар поставщика
    с автоматической ценой виден только при правиле наценки, иначе цена равна закупочной.
    """
    own_stock = (
        select(StockItem.id)
        .join(Warehouse, Warehouse.id == StockItem.warehouse_id)
        .where(
            StockItem.product_id == Product.id,
            StockItem.quantity > StockItem.reserved,
            Warehouse.is_active == True,  # noqa: E712
        )
        .exists()
    )
    partner_stock = (
        select(SupplierOffer.id)
        .join(Supplier, Supplier.id == SupplierOffer.supplier_id)
        .where(
            SupplierOffer.product_id == Product.id,
            SupplierOffer.is_active == True,  # noqa: E712
            SupplierOffer.quantity > 0,
            Supplier.is_active == True,  # noqa: E712
            Supplier.show_on_storefront == True,  # noqa: E712
        )
        .exists()
    )
    priced = or_(
        Product.is_price_manual == True,  # noqa: E712
        select(PricingRule.id)
        .where(or_(PricingRule.category_id.is_(None), PricingRule.category_id == Product.category_id))
        .exists(),
    )
    return [
        Product.status == ProductStatusEnum.published.value,
        Product.category_id.in_(_active_category_ids()),
        or_(own_stock, and_(partner_stock, priced)),
    ]


class CatalogRepository(BaseRepository):

    async def get_active_categories(self) -> list[Category]:
        result = await self.db.execute(
            select(Category)
            .where(Category.is_active == True)  # noqa: E712
            .order_by(Category.position, Category.name)
        )
        return list(result.scalars().all())

    async def get_visible_category_ids(self) -> set[int]:
        """Разделы, в которых прямо сейчас есть что купить."""
        result = await self.db.execute(
            select(Product.category_id).where(*visible_product_conditions()).distinct()
        )
        return set(result.scalars().all())

    async def get_category_photos(self) -> dict[int, tuple[str, float]]:
        """
        Фото самого ходового товара с фото в каждом разделе, где есть что купить.
        Своё фото или, пока его нет, фото поставщика по ссылке.

        Ходовой — с наибольшим остатком у поставщика: этот товар точно есть и он популярный.
        Возвращает раздел → (фото, остаток), остаток нужен, чтобы выбрать лучшее из подразделов.
        """
        stock = (
            select(func.coalesce(func.max(SupplierOffer.quantity), 0))
            .where(SupplierOffer.product_id == Product.id, SupplierOffer.is_active == True)  # noqa: E712
            .scalar_subquery()
        )
        picture = product_picture()
        result = await self.db.execute(
            select(Product.category_id, picture, stock)
            .where(*visible_product_conditions(), picture.is_not(None))
            .distinct(Product.category_id)
            .order_by(Product.category_id, stock.desc(), Product.id)
        )
        return {category_id: (image, float(score)) for category_id, image, score in result.all()}

    async def get_published_products(
        self,
        category_slug: str | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[Product], int]:
        """Товары, которые можно купить. Раздел включает свои подразделы."""
        conditions = visible_product_conditions()
        if category_slug:
            conditions.append(Product.category_id.in_(_category_subtree_ids(category_slug)))
        if search:
            conditions.append(Product.name.icontains(search, autoescape=True))

        total = await self.db.execute(select(func.count(Product.id)).where(*conditions))
        result = await self.db.execute(
            select(Product)
            .where(*conditions)
            # Товары без фото, даже у поставщика, в конце списка
            .order_by(product_picture().is_(None), Product.name, Product.id)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all()), total.scalar() or 0

    async def get_partner_pictures(self, product_ids: list[int]) -> dict[int, str]:
        """Фото поставщика для товаров, у которых ещё нет своего фото."""
        if not product_ids:
            return {}
        result = await self.db.execute(
            select(SupplierOffer.product_id, SupplierOffer.picture_url)
            .where(
                SupplierOffer.product_id.in_(product_ids),
                SupplierOffer.is_active == True,  # noqa: E712
                SupplierOffer.picture_url.is_not(None),
            )
            .distinct(SupplierOffer.product_id)
            .order_by(SupplierOffer.product_id, (SupplierOffer.quantity > 0).desc(), SupplierOffer.id)
        )
        return dict(result.all())

    async def get_published_product_by_slug(self, slug: str) -> Product | None:
        """Карточка открывается и без наличия: ссылки из мессенджеров не должны вести в 404."""
        result = await self.db.execute(
            select(Product).where(
                Product.slug == slug,
                Product.status == ProductStatusEnum.published.value,
            )
        )
        return result.scalar_one_or_none()
