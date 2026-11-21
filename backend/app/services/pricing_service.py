from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pricing import calc_fixed_price, calc_sale_price
from app.models.catalog import Category, Product
from app.models.pricing import ProductPrice
from app.repositories.pricing_repo import PricingRepository
from app.schemas.pricing import (
    PricingRuleIn,
    PricingRuleOut,
    PricingRuleSaveOut,
    ProductPriceIn,
    ProductPriceOut,
)


class PricingService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = PricingRepository(db=db)

    async def list_rules(self) -> list[PricingRuleOut]:
        rules = await self.repo.get_rules()
        return [PricingRuleOut.model_validate(rule) for rule in rules]

    async def save_rule(self, data: PricingRuleIn) -> PricingRuleSaveOut:
        """Создаёт или меняет правило категории и пересчитывает цены."""
        if data.category_id is not None and await self.db.get(Category, data.category_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

        rule = await self.repo.get_rule_by_category_for_update(category_id=data.category_id)
        if rule is None:
            rule = await self.repo.create_rule(**data.model_dump())
        else:
            rule.markup_percent = data.markup_percent
            rule.min_profit = data.min_profit

        updated = await self.recalc_prices()
        await self.db.commit()
        await self.db.refresh(rule)
        return PricingRuleSaveOut(rule=PricingRuleOut.model_validate(rule), updated_prices=updated)

    async def delete_rule(self, rule_id: int) -> int:
        rule = await self.repo.get_rule(rule_id=rule_id)
        if rule is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pricing rule not found")
        await self.repo.delete_rule(rule)
        updated = await self.recalc_prices()
        await self.db.commit()
        return updated

    async def recalc_prices(self, product_ids: list[int] | None = None) -> int:
        """
        Пересчитывает цены товаров с автоматической ценой. Не делает commit.

        Точная цена товара важнее правил наценки. Товар без точной цены и без активного
        предложения или подходящего правила сохраняет цену: лучше старая цена, чем ноль на витрине.
        """
        products = await self.repo.get_auto_priced_products(product_ids=product_ids)
        if not products:
            return 0
        ids = [product.id for product in products]
        offers = await self.repo.get_best_offers(product_ids=ids)
        fixed = await self.repo.get_product_prices(product_ids=ids)
        rules = {rule.category_id: rule for rule in await self.repo.get_rules()}

        updated = 0
        for product in products:
            offer = offers.get(product.id)
            rule = rules.get(product.category_id) or rules.get(None)
            if product.id in fixed:
                row = fixed[product.id]
                price = calc_fixed_price(row.price, offer.price if offer else None, row.min_profit)
            elif offer is not None and rule is not None:
                price = calc_sale_price(offer.price, rule.markup_percent, rule.min_profit)
            else:
                continue
            if price != product.price:
                product.price = price
                updated += 1
        await self.db.flush()
        return updated

    # ─── Точные цены товаров ──────────────────────────────────────────────────

    async def list_product_prices(self) -> list[ProductPriceOut]:
        rows = await self.repo.get_product_prices_with_products()
        offers = await self.repo.get_best_offers(product_ids=[product.id for _, product in rows])
        return [self._product_price_out(row, product, offers.get(product.id)) for row, product in rows]

    async def save_product_price(self, data: ProductPriceIn) -> ProductPriceOut:
        """
        Задаёт товару точную цену и пересчитывает её.

        Товар переходит на автоматическую цену: иначе пересчёт его не трогает и минимум
        прибыли не сработает.
        """
        product = await self.db.get(Product, data.product_id)
        if product is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

        row = await self.repo.get_product_price_for_update(product_id=product.id)
        if row is None:
            row = await self.repo.create_product_price(**data.model_dump())
        else:
            row.price = data.price
            row.min_profit = data.min_profit
        product.is_price_manual = False
        await self.db.flush()
        await self.recalc_prices(product_ids=[product.id])
        await self.db.commit()
        await self.db.refresh(row)
        await self.db.refresh(product)

        offers = await self.repo.get_best_offers(product_ids=[product.id])
        return self._product_price_out(row, product, offers.get(product.id))

    async def delete_product_price(self, product_id: int) -> None:
        """Убирает точную цену: товар возвращается к наценке своей категории."""
        row = await self.repo.get_product_price_for_update(product_id=product_id)
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product price not found")
        await self.repo.delete_product_price(row)
        await self.recalc_prices(product_ids=[product_id])
        await self.db.commit()

    @staticmethod
    def _product_price_out(row: ProductPrice, product: Product, offer) -> ProductPriceOut:
        return ProductPriceOut(
            product_id=product.id,
            product_name=product.name,
            product_sku=product.sku,
            price=row.price,
            min_profit=row.min_profit,
            sale_price=product.price,
            cost=offer.price if offer else None,
            is_price_manual=product.is_price_manual,
            updated_at=row.updated_at,
        )
