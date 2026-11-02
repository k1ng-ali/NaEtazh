import secrets

from fastapi import HTTPException, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.media import InvalidImageError, compress_image, delete_media, save_media
from app.core.slug import slugify
from app.models.catalog import Product
from app.repositories.admin_catalog_repo import AdminCatalogRepository
from app.schemas.admin_catalog import (
    CategoryIn,
    CategoryOutAdmin,
    CategoryUpdate,
    ProductIn,
    ProductListOutAdmin,
    ProductOfferOut,
    ProductOutAdmin,
    ProductRowAdmin,
    ProductUpdate,
    StockIn,
    StockOut,
    WarehouseOut,
)
from app.services.pricing_service import PricingService

MAX_PRODUCT_IMAGES = 10


class AdminCatalogService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = AdminCatalogRepository(db=db)

    # ─── Категории ────────────────────────────────────────────────────────────

    async def list_categories(self) -> list[CategoryOutAdmin]:
        rows = await self.repo.get_categories_with_counts()
        return [
            CategoryOutAdmin.model_validate(category).model_copy(update={"product_count": count})
            for category, count in rows
        ]

    async def create_category(self, data: CategoryIn) -> CategoryOutAdmin:
        if data.parent_id is not None:
            await self._get_category_or_404(data.parent_id)
        slug = data.slug or slugify(data.name)
        if await self.repo.category_slug_exists(slug=slug):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Category slug already exists")

        category = await self.repo.create_category(**data.model_dump(exclude={"slug"}), slug=slug)
        await self.db.commit()
        return CategoryOutAdmin.model_validate(category)

    async def update_category(self, category_id: int, data: CategoryUpdate) -> CategoryOutAdmin:
        category = await self._get_category_or_404(category_id)
        values = data.model_dump(exclude_unset=True)

        if values.get("parent_id") is not None:
            if values["parent_id"] == category_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT, detail="Category cannot be its own parent"
                )
            await self._get_category_or_404(values["parent_id"])
        if "slug" in values and await self.repo.category_slug_exists(
            slug=values["slug"], exclude_id=category_id
        ):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Category slug already exists")
        for field in ("name", "slug", "position", "is_active"):
            if values.get(field) is None:
                values.pop(field, None)

        for field, value in values.items():
            setattr(category, field, value)
        await self.db.commit()
        await self.db.refresh(category)
        count = await self.repo.count_category_products(category_id=category_id)
        return CategoryOutAdmin.model_validate(category).model_copy(update={"product_count": count})

    async def delete_category(self, category_id: int) -> None:
        category = await self._get_category_or_404(category_id)
        if await self.repo.count_category_products(category_id=category_id):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Category has products")
        categories = await self.repo.get_categories_with_counts()
        if any(item.parent_id == category_id for item, _ in categories):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Category has subcategories")
        await self.repo.delete_category(category)
        await self.db.commit()

    # ─── Товары ───────────────────────────────────────────────────────────────

    async def list_products(
        self,
        search: str | None = None,
        category_id: int | None = None,
        status: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> ProductListOutAdmin:
        rows, total = await self.repo.get_products(
            search=search,
            category_id=category_id,
            status=status,
            skip=skip,
            limit=limit,
        )
        items = [
            ProductRowAdmin(
                id=product.id,
                category_id=product.category_id,
                sku=product.sku,
                name=product.name,
                unit=product.unit,
                price=product.price,
                is_price_manual=product.is_price_manual,
                status=product.status,
                image=product.images[0] if product.images else None,
                stock_quantity=stock_quantity,
                offer_price=offer_price,
                offer_quantity=offer_quantity,
            )
            for product, stock_quantity, offer_price, offer_quantity in rows
        ]
        return ProductListOutAdmin(items=items, total=total)

    async def get_product(self, product_id: int) -> ProductOutAdmin:
        product = await self._get_product_or_404(product_id)
        return await self._product_out(product)

    async def create_product(self, data: ProductIn) -> ProductOutAdmin:
        await self._get_category_or_404(data.category_id)
        sku = data.sku.strip() if data.sku and data.sku.strip() else await self._generate_sku()
        if await self.repo.product_field_exists("sku", sku):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Product SKU already exists")
        slug = data.slug or await self._unique_product_slug(data.name)
        if await self.repo.product_field_exists("slug", slug):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Product slug already exists")

        product = await self.repo.create_product(
            **data.model_dump(exclude={"sku", "slug", "status"}),
            sku=sku,
            slug=slug,
            status=data.status.value,
            images=[],
        )
        await self.db.commit()
        return await self._product_out(product)

    async def update_product(self, product_id: int, data: ProductUpdate) -> ProductOutAdmin:
        product = await self._get_product_or_404(product_id)
        values = data.model_dump(exclude_unset=True)

        # Обязательные поля нельзя очистить
        for field in ("category_id", "name", "sku", "slug", "unit", "price", "is_price_manual", "status"):
            if field in values and values[field] is None:
                values.pop(field)
        if "category_id" in values:
            await self._get_category_or_404(values["category_id"])
        for field in ("sku", "slug"):
            if field in values and await self.repo.product_field_exists(field, values[field], product_id):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT, detail=f"Product {field} already exists"
                )

        removed_images: list[str] = []
        if "images" in values:
            images = values["images"] or []
            # Через этот метод фото только переставляют и удаляют, новые идут через загрузку
            if not set(images) <= set(product.images) or len(set(images)) != len(images):
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Unknown image")
            removed_images = [url for url in product.images if url not in images]
            values["images"] = images
        if "status" in values:
            values["status"] = values["status"].value

        switched_to_auto = values.get("is_price_manual") is False and product.is_price_manual
        for field, value in values.items():
            setattr(product, field, value)
        await self.db.flush()
        if switched_to_auto:
            await PricingService(db=self.db).recalc_prices(product_ids=[product.id])
        await self.db.commit()

        for url in removed_images:
            delete_media(url)
        await self.db.refresh(product)
        return await self._product_out(product)

    async def add_product_image(self, product_id: int, content: bytes) -> ProductOutAdmin:
        product = await self._get_product_or_404(product_id)
        if len(product.images) >= MAX_PRODUCT_IMAGES:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Too many images")
        try:
            compressed = await run_in_threadpool(compress_image, content)
        except InvalidImageError as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc

        url = await run_in_threadpool(save_media, compressed, "products")
        product.images = [*product.images, url]
        try:
            await self.db.commit()
        except Exception:
            delete_media(url)
            raise
        await self.db.refresh(product)
        return await self._product_out(product)

    # ─── Склад ────────────────────────────────────────────────────────────────

    async def list_warehouses(self) -> list[WarehouseOut]:
        warehouses = await self.repo.get_warehouses()
        return [WarehouseOut.model_validate(item) for item in warehouses]

    async def set_stock(self, product_id: int, data: StockIn) -> ProductOutAdmin:
        product = await self._get_product_or_404(product_id)
        if await self.repo.get_warehouse(data.warehouse_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found")

        item = await self.repo.get_stock_item_for_update(
            warehouse_id=data.warehouse_id, product_id=product_id
        )
        if item is None:
            await self.repo.create_stock_item(
                warehouse_id=data.warehouse_id,
                product_id=product_id,
                quantity=data.quantity,
                unit_cost=data.unit_cost,
            )
        else:
            # Резерв под заказы не может превышать остаток
            if data.quantity < item.reserved:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT, detail="Quantity is less than reserved"
                )
            item.quantity = data.quantity
            item.unit_cost = data.unit_cost
        await self.db.commit()
        return await self._product_out(product)

    # ─── Хелперы ──────────────────────────────────────────────────────────────

    async def _get_category_or_404(self, category_id: int):
        category = await self.repo.get_category(category_id)
        if category is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
        return category

    async def _get_product_or_404(self, product_id: int) -> Product:
        product = await self.repo.get_product(product_id)
        if product is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        return product

    async def _generate_sku(self) -> str:
        while True:
            sku = f"SB-{secrets.token_hex(3).upper()}"
            if not await self.repo.product_field_exists("sku", sku):
                return sku

    async def _unique_product_slug(self, name: str) -> str:
        base = slugify(name)
        slug, suffix = base, 2
        while await self.repo.product_field_exists("slug", slug):
            slug, suffix = f"{base}-{suffix}", suffix + 1
        return slug

    async def _product_out(self, product: Product) -> ProductOutAdmin:
        stock = await self.repo.get_product_stock(product_id=product.id)
        offers = await self.repo.get_product_offers(product_id=product.id)
        return ProductOutAdmin.model_validate(product).model_copy(
            update={
                "stock": [
                    StockOut(
                        warehouse_id=item.warehouse_id,
                        warehouse_name=name,
                        quantity=item.quantity,
                        reserved=item.reserved,
                        unit_cost=item.unit_cost,
                    )
                    for item, name in stock
                ],
                "offers": [
                    ProductOfferOut(
                        id=offer.id,
                        supplier_name=supplier_name,
                        name=offer.name,
                        url=offer.url,
                        price=offer.price,
                        quantity=offer.quantity,
                        is_active=offer.is_active,
                    )
                    for offer, supplier_name in offers
                ],
            }
        )
