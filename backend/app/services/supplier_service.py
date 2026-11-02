from datetime import datetime, timezone

import httpx
from fastapi import HTTPException, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.slug import slugify
from app.core.yml_feed import FeedError, FeedOffer, parse_yml
from app.enums.product_status import ProductStatusEnum
from app.models.inventory import Supplier, SupplierOffer
from app.repositories.admin_catalog_repo import AdminCatalogRepository
from app.repositories.supplier_repo import SupplierRepository
from app.schemas.supplier import (
    OfferCreateProductOut,
    OfferListOut,
    OfferOut,
    SupplierOut,
    SupplierSyncOut,
)
from app.services.pricing_service import PricingService

FEED_TIMEOUT_SECONDS = 60
MAX_FEED_BYTES = 50 * 1024 * 1024
# Если выгрузка внезапно стала вдвое меньше, скорее всего она сломана, а не товары кончились
MIN_FEED_SHARE = 0.5
MIN_OFFERS_FOR_SHARE_CHECK = 100

_SYNC_FIELDS = ("name", "url", "vendor", "category_name", "picture_url", "weight_kg", "price", "quantity")


async def download_feed(url: str) -> bytes:
    async with httpx.AsyncClient(timeout=FEED_TIMEOUT_SECONDS, follow_redirects=True) as client:
        async with client.stream("GET", url) as response:
            response.raise_for_status()
            chunks, size = [], 0
            async for chunk in response.aiter_bytes():
                size += len(chunk)
                if size > MAX_FEED_BYTES:
                    raise FeedError("Выгрузка больше 50 МБ")
                chunks.append(chunk)
    return b"".join(chunks)


class SupplierService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = SupplierRepository(db=db)

    # ─── Поставщики и импорт ──────────────────────────────────────────────────

    async def list_suppliers(self) -> list[SupplierOut]:
        rows = await self.repo.get_suppliers_with_counts()
        return [self._supplier_out(supplier, active, unmatched) for supplier, active, unmatched in rows]

    async def sync_supplier(self, supplier_id: int) -> SupplierSyncOut:
        """
        Загружает выгрузку и обновляет предложения.

        При любой ошибке старые цены и остатки остаются, причина сохраняется у поставщика.
        """
        supplier = await self._get_supplier_or_404(supplier_id)
        if not supplier.feed_url:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Supplier has no feed")

        try:
            content = await download_feed(supplier.feed_url)
            feed = await run_in_threadpool(parse_yml, content)
            existing = await self.repo.get_supplier_offers(supplier_id=supplier_id)
            self._check_feed_size(feed=feed, active_before=sum(1 for offer in existing if offer.is_active))
        except (httpx.HTTPError, FeedError) as exc:
            supplier.last_sync_error = self._error_text(exc)
            await self.db.commit()
            return await self._sync_out(supplier_id=supplier_id, ok=False, error=supplier.last_sync_error)

        try:
            supplier = await self.repo.get_supplier_for_update(supplier_id=supplier_id)
        except DBAPIError as exc:
            await self.db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Sync already running") from exc

        summary = self._apply_feed(supplier_id=supplier_id, feed=feed, existing=existing)
        await self.db.flush()
        summary["prices_updated"] = await PricingService(db=self.db).recalc_prices()

        supplier.last_synced_at = datetime.now(timezone.utc)
        supplier.last_sync_error = None
        supplier.last_sync_summary = summary
        await self.db.commit()
        return await self._sync_out(supplier_id=supplier_id, ok=True)

    async def sync_all(self) -> list[SupplierSyncOut]:
        """Для запуска по расписанию."""
        return [
            await self.sync_supplier(supplier_id) for supplier_id in await self.repo.get_active_supplier_ids()
        ]

    # ─── Предложения и сопоставление ──────────────────────────────────────────

    async def list_offers(
        self,
        supplier_id: int | None = None,
        match: str = "all",
        search: str | None = None,
        in_stock: bool = False,
        skip: int = 0,
        limit: int = 50,
    ) -> OfferListOut:
        rows, total = await self.repo.get_offers(
            supplier_id=supplier_id,
            match=match,
            search=search,
            in_stock=in_stock,
            skip=skip,
            limit=limit,
        )
        return OfferListOut(items=[self._offer_out(offer, name) for offer, name in rows], total=total)

    async def link_offer(self, offer_id: int, product_id: int) -> OfferOut:
        offer = await self._get_offer_or_404(offer_id)
        product = await self.repo.get_product(product_id)
        if product is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

        offer.product_id = product.id
        await self.db.flush()
        await PricingService(db=self.db).recalc_prices(product_ids=[product.id])
        await self.db.commit()
        return self._offer_out(offer, product.name)

    async def unlink_offer(self, offer_id: int) -> OfferOut:
        offer = await self._get_offer_or_404(offer_id)
        # Цена товара остаётся прежней, менеджер решит, что с ним делать
        offer.product_id = None
        await self.db.commit()
        return self._offer_out(offer, None)

    async def create_product_from_offer(self, offer_id: int, category_id: int) -> OfferCreateProductOut:
        """Черновик товара витрины из предложения. Фото партнёра не копируем без его разрешения."""
        offer = await self._get_offer_or_404(offer_id)
        if offer.product_id is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Offer already linked")

        catalog_repo = AdminCatalogRepository(db=self.db)
        if await catalog_repo.get_category(category_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

        base_slug = slugify(offer.name)
        slug, suffix = base_slug, 2
        while await catalog_repo.product_field_exists("slug", slug):
            slug, suffix = f"{base_slug}-{suffix}", suffix + 1
        sku = f"FA-{offer.external_id}"
        if await catalog_repo.product_field_exists("sku", sku):
            sku = f"{sku}-{offer.id}"

        product = await catalog_repo.create_product(
            category_id=category_id,
            sku=sku,
            name=offer.name,
            slug=slug,
            unit="шт",
            # Без правила наценки цена равна закупочной, поэтому товар создаётся черновиком
            price=offer.price,
            is_price_manual=False,
            weight_kg=offer.weight_kg,
            images=[],
            attributes={"Бренд": offer.vendor} if offer.vendor else {},
            status=ProductStatusEnum.draft.value,
        )
        offer.product_id = product.id
        await self.db.flush()
        await PricingService(db=self.db).recalc_prices(product_ids=[product.id])
        await self.db.commit()
        return OfferCreateProductOut(product_id=product.id, offer=self._offer_out(offer, product.name))

    # ─── Хелперы ──────────────────────────────────────────────────────────────

    @staticmethod
    def _check_feed_size(feed: list[FeedOffer], active_before: int) -> None:
        if not feed:
            raise FeedError("В выгрузке нет ни одного товара")
        if active_before >= MIN_OFFERS_FOR_SHARE_CHECK and len(feed) < active_before * MIN_FEED_SHARE:
            raise FeedError(
                f"В выгрузке {len(feed)} товаров вместо {active_before}. "
                "Похоже на сбой у партнёра, данные не изменены"
            )

    def _apply_feed(self, supplier_id: int, feed: list[FeedOffer], existing: list[SupplierOffer]) -> dict:
        now = datetime.now(timezone.utc)
        by_external_id = {offer.external_id: offer for offer in existing}
        feed_by_id = {item.external_id: item for item in feed}
        created = updated = hidden = 0

        new_offers = []
        for external_id, item in feed_by_id.items():
            offer = by_external_id.get(external_id)
            if offer is None:
                new_offers.append(
                    SupplierOffer(
                        supplier_id=supplier_id,
                        external_id=external_id,
                        is_active=True,
                        last_seen_at=now,
                        **{field: getattr(item, field) for field in _SYNC_FIELDS},
                    )
                )
                created += 1
                continue

            if offer.price != item.price or offer.quantity != item.quantity or not offer.is_active:
                updated += 1
            for field in _SYNC_FIELDS:
                setattr(offer, field, getattr(item, field))
            offer.is_active = True
            offer.last_seen_at = now

        # Пропавшие из выгрузки скрываем, а не удаляем: на них ссылаются товары и заказы
        for offer in existing:
            if offer.external_id not in feed_by_id and offer.is_active:
                offer.is_active = False
                hidden += 1

        self.db.add_all(new_offers)
        return {"total": len(feed_by_id), "created": created, "updated": updated, "hidden": hidden}

    async def _get_supplier_or_404(self, supplier_id: int) -> Supplier:
        supplier = await self.repo.get_supplier(supplier_id)
        if supplier is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supplier not found")
        return supplier

    async def _get_offer_or_404(self, offer_id: int) -> SupplierOffer:
        offer = await self.repo.get_offer(offer_id)
        if offer is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found")
        return offer

    async def _sync_out(self, supplier_id: int, ok: bool, error: str | None = None) -> SupplierSyncOut:
        rows = await self.repo.get_suppliers_with_counts()
        supplier, active, unmatched = next(row for row in rows if row[0].id == supplier_id)
        return SupplierSyncOut(ok=ok, error=error, supplier=self._supplier_out(supplier, active, unmatched))

    @staticmethod
    def _error_text(exc: Exception) -> str:
        if isinstance(exc, httpx.HTTPStatusError):
            return f"Сайт партнёра ответил ошибкой {exc.response.status_code}"
        if isinstance(exc, httpx.HTTPError):
            return "Сайт партнёра недоступен"
        return str(exc)[:500]

    @staticmethod
    def _supplier_out(supplier: Supplier, active: int, unmatched: int) -> SupplierOut:
        return SupplierOut.model_validate(supplier).model_copy(
            update={"offers_active": active, "offers_unmatched": unmatched}
        )

    @staticmethod
    def _offer_out(offer: SupplierOffer, product_name: str | None) -> OfferOut:
        return OfferOut.model_validate(offer).model_copy(update={"product_name": product_name})
