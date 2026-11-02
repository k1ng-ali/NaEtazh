from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pricing import calc_sale_price
from app.models.catalog import Category
from app.repositories.pricing_repo import PricingRepository
from app.schemas.pricing import PricingRuleIn, PricingRuleOut, PricingRuleSaveOut


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

        Товар без активного предложения или без подходящего правила сохраняет цену:
        лучше старая цена, чем ноль на витрине.
        """
        products = await self.repo.get_auto_priced_products(product_ids=product_ids)
        if not products:
            return 0
        offers = await self.repo.get_best_offers(product_ids=[product.id for product in products])
        rules = {rule.category_id: rule for rule in await self.repo.get_rules()}

        updated = 0
        for product in products:
            offer = offers.get(product.id)
            rule = rules.get(product.category_id) or rules.get(None)
            if offer is None or rule is None:
                continue
            price = calc_sale_price(offer.price, rule.markup_percent, rule.min_profit)
            if price != product.price:
                product.price = price
                updated += 1
        await self.db.flush()
        return updated
