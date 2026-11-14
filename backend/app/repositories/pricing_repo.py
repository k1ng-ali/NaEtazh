from sqlalchemy import select

from app.models.catalog import Product
from app.models.inventory import Supplier, SupplierOffer
from app.models.pricing import PricingRule
from app.repositories.base_repo import BaseRepository


class PricingRepository(BaseRepository):

    async def get_rules(self) -> list[PricingRule]:
        result = await self.db.execute(
            select(PricingRule).order_by(PricingRule.category_id.is_not(None), PricingRule.id)
        )
        return list(result.scalars().all())

    async def get_rule(self, rule_id: int) -> PricingRule | None:
        return await self.db.get(PricingRule, rule_id)

    async def get_rule_by_category_for_update(self, category_id: int | None) -> PricingRule | None:
        condition = (
            PricingRule.category_id.is_(None)
            if category_id is None
            else PricingRule.category_id == category_id
        )
        result = await self.db.execute(select(PricingRule).where(condition).with_for_update())
        return result.scalar_one_or_none()

    async def create_rule(self, **values) -> PricingRule:
        rule = PricingRule(**values)
        self.db.add(rule)
        await self.db.flush()
        await self.db.refresh(rule)
        return rule

    async def delete_rule(self, rule: PricingRule) -> None:
        await self.db.delete(rule)
        await self.db.flush()

    async def get_auto_priced_products(self, product_ids: list[int] | None = None) -> list[Product]:
        query = select(Product).where(Product.is_price_manual == False)  # noqa: E712
        if product_ids is not None:
            query = query.where(Product.id.in_(product_ids))
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_best_offers(
        self, product_ids: list[int], storefront_only: bool = False
    ) -> dict[int, SupplierOffer]:
        """
        Предложение партнёра, от которого считаем цену: сначала с остатком, затем дешевле.

        storefront_only: только поставщики, включённые на витрине, — из них можно продавать.
        """
        if not product_ids:
            return {}
        query = select(SupplierOffer).where(
            SupplierOffer.product_id.in_(product_ids),
            SupplierOffer.is_active == True,  # noqa: E712
        )
        if storefront_only:
            query = query.join(Supplier, Supplier.id == SupplierOffer.supplier_id).where(
                Supplier.is_active == True,  # noqa: E712
                Supplier.show_on_storefront == True,  # noqa: E712
            )
        result = await self.db.execute(
            query.distinct(SupplierOffer.product_id).order_by(
                SupplierOffer.product_id, (SupplierOffer.quantity > 0).desc(), SupplierOffer.price
            )
        )
        return {offer.product_id: offer for offer in result.scalars().all()}

    async def get_sellable_offers(self, products: list[Product]) -> dict[int, SupplierOffer]:
        """
        Предложения, из которых можно продавать покупателю.

        Поставщик включён на витрине, а цена товара задана вручную или посчитана по наценке:
        без правила наценки автоматическая цена равна закупочной.
        """
        offers = await self.get_best_offers([product.id for product in products], storefront_only=True)
        if not offers:
            return {}
        rule_categories = {rule.category_id for rule in await self.get_rules()}
        priced = {
            product.id
            for product in products
            if product.is_price_manual or None in rule_categories or product.category_id in rule_categories
        }
        return {product_id: offer for product_id, offer in offers.items() if product_id in priced}
